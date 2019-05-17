# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from welfareFilm import items

class MovieSpider(CrawlSpider):
    name = 'movie'
    allowed_domains = ['riri189.com']
    start_urls = (
        'https://riri189.com/vodtypehtml/1.html',
        'https://riri189.com/vodtypehtml/2.html',
        'https://riri189.com/vodtypehtml/3.html',
        'https://riri189.com/vodtypehtml/4.html',
        'https://riri189.com/vodtypehtml/5.html',
        'https://riri189.com/vodtypehtml/6.html',
        'https://riri189.com/vodtypehtml/7.html',
        'https://riri189.com/vodtypehtml/9.html',
    )


    rules = (
        Rule(LinkExtractor(allow=r'/vodtypehtml/\d+-\d+\.html'),callback='parse_item',follow=True),
        # Rule(LinkExtractor(allow=r'/vodplayhtml/\d+\.html\?\d+-1-1'), ),
    )

    def parse_item(self, response):
        print(response.url)
        type = response.xpath('//h1/a[2]/text()').extract()
        print('type',type)
        # return True
        for each in response.xpath('//div[@class="item"]'):
            item = items.WelfarefilmItem()
            # 标题
            item['title'] = each.xpath('./a//strong/text()').extract()[0]
            # 播放链接
            item['play_url'] = 'https://riri189.com'+each.xpath('./a/@href').extract()[0]
            # 封面
            item['cover'] = each.xpath('./a//img[@class="thumb lazy-load"]/@src').extract()[0]
            # 上映时间
            item['release_date'] = each.xpath('./a//div[@class="added"]/em/text()').extract()[0]
            # 类型
            item['type'] = type
            yield item
