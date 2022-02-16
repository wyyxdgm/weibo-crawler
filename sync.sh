#!/bin/bash

rsync -avz --progress . root@101.43.109.138:jobs-crawler --exclude weibo --exclude .git --exclude config.json --exclude all.log --exclude error.log --exclude user_id_list.txt --exclude all-get-jobs.log --exclude error-get-jobs.log
rsync -avz --progress config.prod.json root@101.43.109.138:jobs-crawler/config.json