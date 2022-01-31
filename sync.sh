#!/bin/bash

rsync -avz --progress . root@101.43.109.138:weibo-crawler --exclude weibo --exclude .git