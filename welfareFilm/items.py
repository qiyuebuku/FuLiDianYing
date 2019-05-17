# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WelfarefilmItem(scrapy.Item):
    # 标题
    title = scrapy.Field()
    # 类型
    type = scrapy.Field()
    # 播放链接
    play_url = scrapy.Field()
    # 下载链接
    dowload_link = scrapy.Field()
    # 封面
    cover = scrapy.Field()
    # 上映时间
    release_date = scrapy.Field()
