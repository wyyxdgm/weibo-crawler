#!/bin/bash

rsync -avz --progress . root@101.43.109.138:weibo-crawler --exclude weibo --exclude .git --exclude config.json --exclude all.log --exclude error.log --exclude user_id_list.txt
rsync -avz --progress config.prod.json root@101.43.109.138:weibo-crawler/config.json