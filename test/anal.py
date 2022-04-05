from lxml import etree
import os
import json
import logging
# import xmltodict
import logging.config
import warnings
warnings.filterwarnings("ignore")
# bb = os.path.abspath(os.path.join(
#     os.path.split(os.path.realpath(__file__))[0], '..'))
logging_path = os.getcwd() + os.sep + 'logging.conf'
logging.config.fileConfig(logging_path)
logger = logging.getLogger('test')


# def xmltojson(xmlstr):
#   xmlparse = xmltodict.parse(xmlstr, encoding='utf-8')
#   jsonstr = json.dumps(xmlparse, indent=1)
#   return jsonstr

def get_child_of_one_node(node):
    """换行元素返回数组，行内元素返回str"""
    selector = etree.ElementTree(node)
    nodesInNode = selector.xpath('child::*')
    if not nodesInNode:
        return selector.xpath('string(.)')
    return resolve_nodes(nodesInNode)


def resolve_nodes(nodes):
    """处理多节点，换行元素返回数组，行内元素返回str"""
    res = []
    for oneNode in nodes:
        if oneNode.tag == 'br':
            if len(res) == 0 or res[-1] != '':
                res.append('')
        else:
            subRes = get_child_of_one_node(oneNode)
            if subRes:
                if isinstance(subRes, list):
                    res.extend(subRes)
                    # i += len(subRes)
                else:
                    if len(res) == 0:
                        res.append(subRes)
                    else:
                        res[-1] += subRes

                    # get_child_of_one_node
    return res

strs = [
    '<a  href="https://m.weibo.cn/p/index?extparam=%E6%A3%89%E8%8A%B1%E7%BE%8E%E5%A8%83%E5%A8%83&containerid=100808da80b66fe1ef587d20501424cbca9198&luicode=20000061&lfid=4753573398972973" data-hide=""><span class=\'url-icon\'><img style=\'width: 1rem;height: 1rem\' src=\'https://n.sinaimg.cn/photo/5213b46e/20180926/timeline_card_small_super_default.png\'></span><span class="surl-text">棉花美娃娃</span></a> 🎁<a  href="https://m.weibo.cn/search?containerid=231522type%3D1%26t%3D10%26q%3D%23%E6%AF%8F%E6%97%A5%E5%A8%83%E8%A1%A3%E5%AE%89%E5%88%A9%23&extparam=%23%E6%AF%8F%E6%97%A5%E5%A8%83%E8%A1%A3%E5%AE%89%E5%88%A9%23&luicode=20000061&lfid=4753573398972973" data-hide=""><span class="surl-text">#每日娃衣安利#</span></a>【投稿】<br /><br />              🍯 等等虎虎崽一起出发趴体呀 🍩 <br /><br /> 卷 🌼➕🍎 论➕⭕1娃友➕关<a href=\'/n/壬寅小夜曲-3-\'>@壬寅小夜曲-3-</a> <br />  🛒【0417】🈵50/100/200揪赠1/2/3位娃衣✖️1<br /><br />🧸 娃衣名称：春日部熊熊&amp;仲夏知兔兔                           金风虎崽崽&amp;玉露虎囡囡 <br />📐 尺  寸：20cm(详情见宣图😉)<br />👛 价  格：单套包u<br />熊熊&amp;兔兔<br />🈶大全套『单套低至: 58r』<br />🈚发带款『单套低至: 51r』<br />崽崽&amp;囡囡<br />🈶大全套『单套低至: 75r』 <br />🈚配饰款『单套低至: 68r』     <br />📦 数  量：限时不限量<br /><br />🎪 wei dian/桃 宝：壬寅小夜曲<br />💫 微  博：<a href=\'/n/壬寅小夜曲-3-\'>@壬寅小夜曲-3-</a><br />    🐧   裙：255654982（蹲蹲裙）<br />📅 时  间：4月3号20: 00至4月17号23: 59<br />📤 工  期：待定<br />💌 其  他：⭐店开业有浮力，有买就有蛰扣哦！',
    '恭喜<a href=\'/n/一起逃命xxxx\'>@一起逃命xxxx</a> 1名用户获得【笨笨 一套娃衣 一个假发发夹】。微博官方唯一抽奖工具<a href=\'/n/微博抽奖平台\'>@微博抽奖平台</a> 对本次抽奖进行监督，结果公正有效。公示链接：<a data-url="http://t.cn/A6xMOZHf" href="http://t.cn/A6xMOZHf" data-hide=""><span class=\'url-icon\'><img style=\'width: 1rem;height: 1rem\' src=\'https://h5.sinaimg.cn/upload/2015/09/25/3/timeline_card_small_web_default.png\'></span><span class="surl-text">网页链接</span></a>',
    '<a  href="https://m.weibo.cn/p/index?extparam=%E6%A3%89%E8%8A%B1%E5%A8%83%E8%A1%A3%E7%A7%80%E5%9C%BA&containerid=10080873785c7f1a9fc43c56b6a91458a5e31b&luicode=20000061&lfid=4695550610114506" data-hide=""><span class=\'url-icon\'><img style=\'width: 1rem;height: 1rem\' src=\'https://n.sinaimg.cn/photo/5213b46e/20180926/timeline_card_small_super_default.png\'></span><span class="surl-text">棉花娃衣秀场</span></a> 🎁 <a  href="https://m.weibo.cn/search?containerid=231522type%3D1%26t%3D10%26q%3D%23%E6%AF%8F%E6%97%A5%E5%A8%83%E8%A1%A3%E5%AE%89%E5%88%A9%23&extparam=%23%E6%AF%8F%E6%97%A5%E5%A8%83%E8%A1%A3%E5%AE%89%E5%88%A9%23&luicode=20000061&lfid=4695550610114506" data-hide=""><span class="surl-text">#每日娃衣安利#</span></a> 【投稿】<br /><br />         💐甜饼小怪兽双十一🧵货浮力❤️<br /><br />          卷🌸 ➕ 关🐷<a href=\'/n/-甜饼小怪兽-\'>@-甜饼小怪兽-</a>  <br />揪 1⃣️ 人 贝曾 笨笨 ➕ 一套娃衣 ➕ 一个假发发夹<br />          ⏰ 11 月 21 日 卷 🈵️ 111 开 ⏰<br /><br />🧸青山芥（汉服）<br />👛68r包u，头饰需另外加购<br />🍥有🈵136➖12的⭕，领了再下🥚<br /><br />🧸阳光雏菊<br />👛68r包u<br />🍥有🈵68➖4和🈵136➖12的⭕，不可叠加使用，领了再下🥚<br /><br />🧸樱花令（汉服）<br />👛68r包u，头饰需另外加购<br />🍥有🈵136➖12的⭕，领了再下🥚<br /><br />🧸奶糖兔兔<br />👛68r包u<br />🍥有🈵68➖4和🈵136➖12的⭕，不可叠加使用，领了再下🥚<br /><br />🧸独家假发蝴蝶结<br />👛28r包u<br /><br />🧸笨笨<br />📐20cm<br />👛76包u<br />🍥有🈵76➖5和🈵136➖12的⭕，不可叠加使用，领了再下🥚<br /><br />🧸炸毛歪妹<br />📐20cm<br />👛72包u<br />🍥有🈵136➖12的⭕，领了再下🥚有🈵136➖12的⭕，领了再下🥚<br /><br />🎪 wei dian：甜饼小怪兽 <br />💫 微 博：<a href=\'/n/-甜饼小怪兽-\'>@-甜饼小怪兽-</a> <br />🐧 裙：1057119422<br />📅 时 间：10.22<br />📌工期：🧵🔥一周左右发 货，收 到 货请录制开箱视频，无开箱视频 不 售 后！',
    '<a  href="https://m.weibo.cn/p/index?extparam=%E6%A3%89%E8%8A%B1%E5%A8%83%E8%A1%A3%E7%A7%80%E5%9C%BA&containerid=10080873785c7f1a9fc43c56b6a91458a5e31b&luicode=20000061&lfid=4706090468770448" data-hide=""><span class=\'url-icon\'><img style=\'width: 1rem;height: 1rem\' src=\'https://n.sinaimg.cn/photo/5213b46e/20180926/timeline_card_small_super_default.png\'></span><span class="surl-text">棉花娃衣秀场</span></a> 🎁 <a  href="https://m.weibo.cn/p/index?extparam=%E6%A3%89%E8%8A%B1%E5%A8%83%E8%A1%A3%E7%A7%80%E5%9C%BA&containerid=10080873785c7f1a9fc43c56b6a91458a5e31b&luicode=20000061&lfid=4706090468770448" data-hide=""><span class=\'url-icon\'><img style=\'width: 1rem;height: 1rem\' src=\'https://n.sinaimg.cn/photo/5213b46e/20180926/timeline_card_small_super_default.png\'></span><span class="surl-text">棉花娃衣秀场</span></a> 【投稿】<br /><br />        🐰  兔子的毛厚厚但是耳朵小小  🐰<br /><br /> ⏰ 12 月 5 日 卷 🈵️ 200 揪 1⃣️ 人 贝曾 两 套 ⏰<br /><br />🧸 娃衣名称：兔绒大衣<br />📐 尺  寸：20 cm<br />👛 价  格：28 r单价包u<br />📦 数  量：不 限 量<br />📍 构  成：单点<br /><br />🎪 wei dian：mewmewdoki<br />💫 微  博：<a href=\'/n/mewmewdoki\'>@mewmewdoki</a><br />📅 时  间：11.20 20:00-12.5 20:00<br />📤 工  期：一月中旬发 货 <a data-url="http://t.cn/A6xO11Q1" href="http://t.cn/A6xO11Q1" data-hide=""><span class=\'url-icon\'><img style=\'width: 1rem;height: 1rem\' src=\'https://h5.sinaimg.cn/upload/2015/09/25/3/timeline_card_small_web_default.png\'></span><span class="surl-text">抽奖详情</span></a>',
    '<a  href="https://m.weibo.cn/p/index?extparam=%E6%A3%89%E8%8A%B1%E5%A8%83%E8%A1%A3%E7%A7%80%E5%9C%BA&containerid=10080873785c7f1a9fc43c56b6a91458a5e31b&luicode=20000061&lfid=4706086391120036" data-hide=""><span class=\'url-icon\'><img style=\'width: 1rem;height: 1rem\' src=\'https://n.sinaimg.cn/photo/5213b46e/20180926/timeline_card_small_super_default.png\'></span><span class="surl-text">棉花娃衣秀场</span></a> 🎁<a  href="https://m.weibo.cn/search?containerid=231522type%3D1%26t%3D10%26q%3D%23%E6%AF%8F%E6%97%A5%E5%A8%83%E8%A1%A3%E5%AE%89%E5%88%A9%23&extparam=%23%E6%AF%8F%E6%97%A5%E5%A8%83%E8%A1%A3%E5%AE%89%E5%88%A9%23&luicode=20000061&lfid=4706086391120036" data-hide=""><span class="surl-text">#每日娃衣安利#</span></a>【投稿】<br /><br />                      💐 走进了万花筒世界 🔮<br /><br />      卷 🌼【1201】揪赠1位88r店铺抵用券✖️1<br /><br />🧸 娃衣名称：昭和动物连衣裙（两个配色）<br />📐 尺  寸：20cm正常体/胖胖体通穿<br />👛 价  格：59r<br />📦 数  量：各15<br /><br />🧸 娃衣名称：昭和动物两面穿外套（两个配色）<br />📐 尺  寸：20cm正常体/胖胖体通穿<br />👛 价  格：69r<br />📦 数  量：各15<br /><br />🧸 娃衣名称：昭和背带裤/背带裙<br />📐 尺  寸：20cm正常体/胖胖体通穿<br />👛 价  格：68r<br />📦 数  量：各10<br /><br />🧸 娃衣名称：昭和动物毛衣（三款）<br />📐 尺  寸：20cm正常体/胖胖体通穿<br />👛 价  格：36r<br />📦 数  量：各25<br /><br />🧸 娃衣名称：小老虎挂件<br />📐 尺  寸：通用<br />👛 价  格：19.9r<br />📦 数  量：50<br /><br />🎪 wei dian：拖鹅所<br />💫 微  博：<a href=\'/n/企鹅xi\'>@企鹅xi</a><br />📅 时  间：11月18日～12月3日<br />📤 工  期：45天左右（数量少会提前<br />💫🌟🌧️👋期间有满减优慧券在店铺首页领取<br />实付满128赠送娃用蝴蝶结🎀头饰一个',
]

text_body = strs[0]
# result = xmltojson(text_body)
# logger.info(result)
selector = etree.HTML(text_body)
# text = selector.xpath('string(.)')

allnodes = selector.xpath('.')
res = resolve_nodes(allnodes)
logger.info(res)
