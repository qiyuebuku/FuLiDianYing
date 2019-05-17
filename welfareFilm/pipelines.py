# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import requests
import re
import urllib
from scrapy.conf import settings
import pymongo


class WelfarefilmPipeline(object):
    def __init__(self):
        host = settings['MONGODB_HOST']
        port = settings['MONGODB_PORT']
        dbname = settings['MONGODB_DBNAME']
        sheetname = settings['MONGODB_SHEETNAME']
        # 创建数据库连接
        client = pymongo.MongoClient(host, port=port)
        # 指定数据库名称
        mydb = client[dbname]
        # 指定数据表
        self.mysheet = mydb[sheetname]

    def process_item(self, item, spider):
        play_url = item['play_url']
        release_date = item['release_date']
        m3u8_url = self.vlink(play_url, release_date)
        item['dowload_link'] = m3u8_url
        print(dict(item))
        self.mysheet.insert(dict(item))
        return item

    def vlink(self, play_url, release_date):
        try:
            num = re.findall(r'vodplayhtml/(\d+)\.html\?', play_url)[0]
            date = release_date.replace('-', '')
            url = 'https://riri189.com/upload/playdata/{0}/{1}/{1}.js'.format(date, num)
            text = requests.get(url=url).text
            m3u8_url = re.findall("mac_url=unescape\('(.*)'\);", text)[0]
            return urllib.parse.unquote(m3u8_url)
        except Exception as e:
            print("错误：", e)
            return False
