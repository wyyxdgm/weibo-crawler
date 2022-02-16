#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import copy
import csv
from distutils.log import debug
import json
import logging
import logging.config
import math
import os
import random
import sqlite3
import sys
import warnings
from collections import OrderedDict
from datetime import date, datetime, timedelta
from pathlib import Path
from time import sleep

import requests
from lxml import etree
from requests.adapters import HTTPAdapter
from tqdm import tqdm

warnings.filterwarnings("ignore")

logging_path = os.path.split(
    os.path.realpath(__file__))[0] + os.sep + 'logging-get_jobs.conf'
logging.config.fileConfig(logging_path)
logger = logging.getLogger('jobs')


class Jobs(object):
    def __init__(self, config):
        """Jobs类初始化"""
        self.validate_config(config)
        self.filter = config[
            'filter']  # 取值范围为0、1,程序默认值为0,代表要爬取用户的全部微博,1代表只爬取用户的原创微博
        self.remove_html_tag = config[
            'remove_html_tag']  # 取值范围为0、1, 0代表不移除微博中的html tag, 1代表移除
        since_date = config['since_date']
        if isinstance(since_date, int):
            since_date = date.today() - timedelta(since_date)
        since_date = str(since_date)
        self.since_date = since_date  # 起始时间，即爬取发布日期从该值到现在的微博，形式为yyyy-mm-dd
        self.start_page = config.get('start_page',
                                     1)  # 开始爬的页，如果中途被限制而结束可以用此定义开始页码
        # 开启记录抓取到的最新页码，进而可以确认下次的start_page值，默认路径：jobs/${screen_name}/{id}.start-page.json
        self.record_last_page = config.get('record_last_page', 1)
        self.write_mode = config[
            'write_mode']  # 结果信息保存类型，为list形式，可包含csv、mongo和mysql三种类型
        self.original_data_to_mongo = config[
            'original_data_to_mongo']  # 取值范围为0、1, 0代表不存储原始数据到mongo,1代表存储
        self.original_pic_download = config[
            'original_pic_download']  # 取值范围为0、1, 0代表不下载原创微博图片,1代表下载
        self.retweet_pic_download = config[
            'retweet_pic_download']  # 取值范围为0、1, 0代表不下载转发微博图片,1代表下载
        self.original_video_download = config[
            'original_video_download']  # 取值范围为0、1, 0代表不下载原创微博视频,1代表下载
        self.retweet_video_download = config[
            'retweet_video_download']  # 取值范围为0、1, 0代表不下载转发微博视频,1代表下载
        self.download_comment = config['download_comment']  # 1代表下载评论,0代表不下载
        self.comment_max_download_count = config[
            'comment_max_download_count']  # 如果设置了下评论，每条微博评论数会限制在这个值内
        self.result_dir_name = config.get(
            'result_dir_name', 0)  # 结果目录名，取值为0或1，决定结果文件存储在用户昵称文件夹里还是用户id文件夹里
        cookie = config.get('cookie')  # 微博cookie，可填可不填
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
        self.headers = {'User-Agent': user_agent, 'Cookie': cookie}
        self.mysql_config = config.get('mysql_config')  # MySQL数据库连接配置，可以不填
        self.mongo_config = config.get('mongo_config')  # MongoDB数据库连接配置，可以不填
        user_id_list = config['user_id_list']
        query_list = config.get('query_list') or []
        if isinstance(query_list, str):
            query_list = query_list.split(',')
        self.query_list = query_list
        if not isinstance(user_id_list, list):
            if not os.path.isabs(user_id_list):
                user_id_list = os.path.split(
                    os.path.realpath(__file__))[0] + os.sep + user_id_list
            self.user_config_file_path = user_id_list  # 用户配置文件路径
            user_config_list = self.get_user_config_list(user_id_list)
        else:
            self.user_config_file_path = ''
            user_config_list = [{
                'user_id': user_id,
                'since_date': self.since_date,
                'query_list': query_list
            } for user_id in user_id_list]
        self.user_config_list = user_config_list  # 要爬取的微博用户的user_config列表
        self.user_config = {}  # 用户配置,包含用户id和since_date
        self.start_date = ''  # 获取用户第一条微博时的日期
        self.query = ''
        self.user = {}  # 存储目标微博用户信息
        self.got_count = 0  # 存储爬取到的微博数
        self.jobs = []  # 存储爬取到的所有微博信息
        self.jobs_id_list = []  # 存储爬取到的所有微博id
        self.users_by_n = {}  # 存储爬取到的所有@用户，以昵称为key

    def validate_config(self, config):
        """验证配置是否正确"""

        # 验证filter、original_pic_download、retweet_pic_download、original_video_download、retweet_video_download
        argument_list = [
            'filter', 'original_pic_download', 'retweet_pic_download',
            'original_video_download', 'retweet_video_download',
            'download_comment', 'original_data_to_mongo'
        ]
        for argument in argument_list:
            if config[argument] != 0 and config[argument] != 1:
                logger.warning(u'%s值应为0或1,请重新输入', config[argument])
                sys.exit()

        # 验证since_date
        since_date = config['since_date']
        if (not self.is_date(str(since_date))) and (not isinstance(
                since_date, int)):
            logger.warning(u'since_date值应为yyyy-mm-dd形式或整数,请重新输入')
            sys.exit()

        # 验证query_list
        query_list = config.get('query_list') or []
        if (not isinstance(query_list, list)) and (not isinstance(
                query_list, str)):
            logger.warning(u'query_list值应为list类型或字符串,请重新输入')
            sys.exit()

        # 验证write_mode
        write_mode = ['csv', 'json', 'mongo', 'mysql', 'sqlite']
        if not isinstance(config['write_mode'], list):
            sys.exit(u'write_mode值应为list类型')
        for mode in config['write_mode']:
            if mode not in write_mode:
                logger.warning(
                    u'%s为无效模式，请从csv、json、mongo和mysql中挑选一个或多个作为write_mode',
                    mode)
                sys.exit()

        # 验证user_id_list
        user_id_list = config['user_id_list']
        if (not isinstance(user_id_list,
                           list)) and (not user_id_list.endswith('.txt')):
            logger.warning(u'user_id_list值应为list类型或txt文件路径')
            sys.exit()
        if not isinstance(user_id_list, list):
            if not os.path.isabs(user_id_list):
                user_id_list = os.path.split(
                    os.path.realpath(__file__))[0] + os.sep + user_id_list
            if not os.path.isfile(user_id_list):
                logger.warning(u'不存在%s文件', user_id_list)
                sys.exit()

        comment_max_count = config['comment_max_download_count']
        if (not isinstance(comment_max_count, int)):
            logger.warning(u'最大下载评论数应为整数类型')
            sys.exit()
        elif (comment_max_count < 0):
            logger.warning(u'最大下载数应该为正整数')
            sys.exit()

    def is_date(self, since_date):
        """判断日期格式是否正确"""
        try:
            datetime.strptime(since_date, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _get_json(self, params, headers, tt, t):
        """获取网页中json数据"""
        if t > 0:
            url = 'https://m.jobs.cn/api/container/getIndex?'
            r = requests.get(url,
                             params=params,
                             headers=headers or self.headers,
                             verify=False)
            try:
                return r.json()
            except Exception as e:
                logger.error(
                    u'_get_json error:[t=%d,url=%s,res:%s]', t, r.url, r.text)
                sleep((tt - t + 1) * random.randint(1, 30))
                return self._get_json(params, t, t-1)
        logger.error(u'_get_json 结束尝试，共失败%d次。', tt)
        return 0

    def get_json(self, params, headers=None):
        """获取网页中json数据"""
        js = self._get_json(params, headers, 3, 3)
        if not js:
            logger.error(u'get_json 失败')
            sys.exit()
        return js

    def do_fetch_jobs(self):
        logger.info(u'do_fetch_jobs')
        # mongo 已经获取的
        jobs = self.mongo_find('jobs', {})
        map_got = {}
        map_got_by_id = {}
        map_got_new = 0
        for item in jobs:
            # logger.info(u'%s, %s',id, at_users)
            if item.get('id'):
                map_got[item['id']] = 1
                map_got_by_id[item['id']] = item['id']
        

        logger.info(u'{}开始抓取{}'.format('*' * 30, '*' * 30))
        # url = 'http://gwykl.fujian.gov.cn/position'
        page_count = 352
        pages = range(self.user_config['start_page'], page_count + 1)

        for page in tqdm(pages, desc='Progress'):
            js = self.get_jobs_by_page(page)
            if js:
                res = js['data']['userInfo']
                id = 'id'
                map_got[id] = res
                map_got_new += 1
                self.info_to_mongodb('at_users', [res])
                logger.info(u'第%d/%d个用户，获取成功:[%s]%s',
                            page, page_count, res['id'], id, map_got_new)
            else:
                logger.info(u'第%d页中断' % page)
                sys.exit(1)
        logger.info(u'{}结束抓取{}'.format('*' * 30, '*' * 30))
    def get_mongodb_collection(self, collection):
        """将爬取的信息写入MongoDB数据库"""
        try:
            import pymongo
        except ImportError:
            logger.warning(
                u'系统中可能没有安装pymongo库，请先运行 pip install pymongo ，再运行程序')
            sys.exit()
        try:
            from pymongo import MongoClient
            mongo_config = {
                "username": "",
                "password": "",
                # "host": "localhost",
                # "port": 27017,
            }
            if self.mongo_config:
                mongo_config = self.mongo_config
            client = MongoClient(**mongo_config)
            db = client['jobs']
            return db[collection]
        except pymongo.errors.ServerSelectionTimeoutError:
            logger.warning(
                u'系统中可能没有安装或启动MongoDB数据库，请先根据系统环境安装或启动MongoDB，再运行程序')
            sys.exit()

    def get_jobs_by_page(self, page):
        try:
            # headers = copy.deepcopy(self.headers)
            # del headers['Cookie']
            r = requests.get('http://gwykl.fujian.gov.cn/z/api.aspx?action=PositionSearch&page=%d&unitCode=&unitName=&unitType=undefined&unitArea=&unitLevel=&positionCode=&positionName=&departmentId=undefined&examType=&eduStatus=&hJLocation=&sex=undefined&jobYear=&nation=&political=&degree=&eduType=&specialPosition=&specialXQPosition=&specialty=&number=&age=&jsoncallback=jQuery1124011043144207625666_1644986205228&_=1644986205230' % page,
                             params={},
                             headers=self.headers,
                             verify=False)
            logger.info(r.url)
            if r.url == 'https://m.jobs.cn/n/%s' % page:
                if r.text and r.text.index('出错了') > -1 or r.text.index('用户不存在') > -1:
                    logger.info('跳转失败，用户不存在')
                else:
                    logger.info('跳转失败，未知原因')
                    logger.info(r.text)
                    logger.info('*'*50)
                return
            user_id = r.url[len('https://m.jobs.cn/u/'):]
            params = {'containerid': '100505' + user_id}
            return self.get_json(params, headers)
        except Exception as e:
            # 没有cookie会获取失败
            logger.info(
                u'获取微博用户信息，昵称:{nick}'.format(nick=nick))
            logger.info(r.text)
            return None

    def mongo_find(self, collection, query):
        try:
            import pymongo
        except ImportError:
            logger.warning(
                u'系统中可能没有安装pymongo库，请先运行 pip install pymongo ，再运行程序')
            sys.exit()
        try:
            from pymongo import MongoClient
            mongo_config = {
                "username": "",
                "password": "",
                # "host": "localhost",
                # "port": 27017,
            }
            if self.mongo_config:
                mongo_config = self.mongo_config
            client = MongoClient(**mongo_config)
            db = client['jobs']
            collection = db[collection]
            return collection.find(query)
        except Exception as e:
            logger.exception(e)

    def info_to_mongodb(self, collection, info_list):
        """将爬取的信息写入MongoDB数据库"""
        try:
            import pymongo
        except ImportError:
            logger.warning(
                u'系统中可能没有安装pymongo库，请先运行 pip install pymongo ，再运行程序')
            sys.exit()
        try:
            from pymongo import MongoClient
            mongo_config = {
                "username": "",
                "password": "",
                # "host": "localhost",
                # "port": 27017,
            }
            if self.mongo_config:
                mongo_config = self.mongo_config
            client = MongoClient(**mongo_config)
            db = client['jobs']
            collection = db[collection]
            if len(self.write_mode) > 1:
                new_info_list = copy.deepcopy(info_list)
            else:
                new_info_list = info_list
            for info in new_info_list:
                if not collection.find_one({'id': info['id']}):
                    collection.insert_one(info)
                else:
                    collection.update_one({'id': info['id']}, {'$set': info})
        except pymongo.errors.ServerSelectionTimeoutError:
            logger.warning(
                u'系统中可能没有安装或启动MongoDB数据库，请先根据系统环境安装或启动MongoDB，再运行程序')
            sys.exit()

    def mysql_create(self, connection, sql):
        """创建MySQL数据库或表"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                return cursor
        finally:
            connection.close()

    def mysql_create_database(self, mysql_config, sql):
        """创建MySQL数据库"""
        try:
            import pymysql
        except ImportError:
            logger.warning(
                u'系统中可能没有安装pymysql库，请先运行 pip install pymysql ，再运行程序')
            sys.exit()
        try:
            if self.mysql_config:
                mysql_config = self.mysql_config
            connection = pymysql.connect(**mysql_config)
            self.mysql_create(connection, sql)
        except pymysql.OperationalError:
            logger.warning(u'系统中可能没有安装或正确配置MySQL数据库，请先根据系统环境安装或配置MySQL，再运行程序')
            sys.exit()

    def mysql_create_table(self, mysql_config, sql):
        """MySQL指定库执行"""
        import pymysql

        if self.mysql_config:
            mysql_config = self.mysql_config
        mysql_config['db'] = 'jobs'
        connection = pymysql.connect(**mysql_config)
        return self.mysql_create(connection, sql)

    def mysql_insert(self, mysql_config, table, data_list):
        """向MySQL表插入或更新数据"""
        import pymysql

        if len(data_list) > 0:
            keys = ', '.join(data_list[0].keys())
            values = ', '.join(['%s'] * len(data_list[0]))
            if self.mysql_config:
                mysql_config = self.mysql_config
            mysql_config['db'] = 'jobs'
            connection = pymysql.connect(**mysql_config)
            cursor = connection.cursor()
            sql = """INSERT INTO {table}({keys}) VALUES ({values}) ON
                     DUPLICATE KEY UPDATE""".format(table=table,
                                                    keys=keys,
                                                    values=values)
            update = ','.join([
                ' {key} = values({key})'.format(key=key)
                for key in data_list[0]
            ])
            sql += update
            try:
                cursor.executemany(
                    sql, [tuple(data.values()) for data in data_list])
                connection.commit()
            except Exception as e:
                connection.rollback()
                logger.exception(e)
            finally:
                connection.close()

    def jobs_to_mysql(self, wrote_count):
        """将爬取的微博信息写入MySQL数据库"""
        mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '123456',
            'charset': 'utf8mb4'
        }
        # 创建'jobs'表
        create_table = """
                CREATE TABLE IF NOT EXISTS jobs (
                id varchar(20) NOT NULL,
                bid varchar(12) NOT NULL,
                user_id varchar(20),
                screen_name varchar(30),
                text varchar(2000),
                article_url varchar(100),
                topics varchar(200),
                at_users varchar(1000),
                pics varchar(3000),
                video_url varchar(1000),
                location varchar(100),
                created_at DATETIME,
                source varchar(30),
                attitudes_count INT,
                comments_count INT,
                reposts_count INT,
                retweet_id varchar(20),
                PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
        self.mysql_create_table(mysql_config, create_table)
        jobs_list = []
        retweet_list = []
        if len(self.write_mode) > 1:
            info_list = copy.deepcopy(self.jobs[wrote_count:])
        else:
            info_list = self.jobs[wrote_count:]
        for w in info_list:
            if 'retweet' in w:
                w['retweet']['retweet_id'] = ''
                retweet_list.append(w['retweet'])
                w['retweet_id'] = w['retweet']['id']
                del w['retweet']
            else:
                w['retweet_id'] = ''
            jobs_list.append(w)
        # 在'jobs'表中插入或更新微博数据
        self.mysql_insert(mysql_config, 'jobs', retweet_list)
        self.mysql_insert(mysql_config, 'jobs', jobs_list)
        logger.info(u'%d条微博写入MySQL数据库完毕', self.got_count)

    def get_user_config_list(self, file_path):
        """获取文件中的微博id信息"""
        with open(file_path, 'rb') as f:
            try:
                lines = f.read().splitlines()
                lines = [line.decode('utf-8-sig') for line in lines]
            except UnicodeDecodeError:
                logger.error(u'%s文件应为utf-8编码，请先将文件编码转为utf-8再运行程序', file_path)
                sys.exit()
            user_config_list = []
            for line in lines:
                info = line.split(' ')
                if len(info) > 0 and info[0].isdigit():
                    user_config = {}
                    user_config['user_id'] = info[0]
                    if len(info) > 2:
                        if self.is_date(info[2]):
                            user_config['since_date'] = info[2]
                        elif info[2].isdigit():
                            since_date = date.today() - timedelta(int(info[2]))
                            user_config['since_date'] = str(since_date)
                    else:
                        user_config['since_date'] = self.since_date
                    if len(info) > 3 and info[3].isdigit():
                        user_config['start_page'] = int(info[3])
                    else:
                        user_config['start_page'] = self.start_page
                    if len(info) > 4:
                        user_config['query_list'] = info[4].split(',')
                    else:
                        user_config['query_list'] = self.query_list
                    if user_config not in user_config_list:
                        user_config_list.append(user_config)
        return user_config_list

    def initialize_info(self, user_config):
        """初始化爬虫信息"""
        self.jobs = []
        self.user = {}
        self.user_config = user_config
        self.got_count = 0
        self.jobs_id_list = []

    def start(self):
        """运行爬虫"""
        try:
            self.do_fetch_jobs()
            logger.info(u'信息处理完毕')
            logger.info(u'*' * 100)
        except Exception as e:
            logger.exception(e)


def get_config():
    """获取config.json文件信息"""
    config_path = os.path.split(
        os.path.realpath(__file__))[0] + os.sep + 'config.json'
    if not os.path.isfile(config_path):
        logger.warning(u'当前路径：%s 不存在配置文件config.json',
                       (os.path.split(os.path.realpath(__file__))[0] + os.sep))
        sys.exit()
    try:
        with open(config_path, encoding='utf-8') as f:
            config = json.loads(f.read())
            return config
    except ValueError:
        logger.error(u'config.json 格式不正确，请参考 '
                     u'https://github.com/dataabc/jobs-crawler#3程序设置')
        sys.exit()


def main():
    try:
        config = get_config()
        wb = Jobs(config)
        wb.start()  # 爬取微博信息
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
