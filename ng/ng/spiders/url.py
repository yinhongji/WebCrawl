# -*- coding: utf-8 -*-
import scrapy
from ng.items import NgItem
import urlparse
import signal
import sys
from scrapy.selector import Selector
from ng.pipelines import graph_init
from py2neo import *
import re

class UrlSpider(scrapy.Spider):
    name = 'url'
    url_set = set()
    form_set = []

    def __init__(self, url=None,*args, **kwargs): 
        super(UrlSpider, self).__init__(*args, **kwargs) 
        self.start_urls = ['%s' % url]
        self.root_url = url
        self.status_root = urlparse.urlparse(url) 
        graph = graph_init()
        node_root = Node('url',name=url)
        node_root['root_url'] = 1
        node_root['login_username_0'] = 'null'
        graph.create(node_root)       

    def myHandler(self, signum , frame):
        self.crawler.engine.close_spider(self, 'Spider exiting...')

    def form_include(self , form_set , form):
        for x in form_set:
            '''
            判断form表单是否重复
            '''
            if x == form:
                return False
        return True

    def parse(self, response):
        url_list = response.xpath('//a/@href').extract()
        form_list = response.xpath('//form').extract()
        url_result , form_result = [] , []
        for form in form_list:
            form_selector = Selector(text=form)
            action = form_selector.xpath('//form/@action').extract()[0]
            if urlparse.urlparse(action).netloc == '' :#and urlparse.urlparse(action).path == '':
                action = urlparse.urljoin(self.root_url,action) 
            param_type = form_selector.xpath('//form/@method').extract()[0]
            param_list = form_selector.xpath('//input').extract()
            result = {}
            for param in param_list:
                param_selector = Selector(text=param)
                name = param_selector.xpath('//input/@name').extract()
                value = param_selector.xpath('//input/@value').extract()
                if name:
                    name = name[0]
                    if value:
                        #form表单中value可为空
                        value = value[0]
                    else:
                        value = ''
                    result[name] = value
            form_three = [action , param_type , result]
            #表单三元组
            if self.form_include(self.form_set , form_three):
                self.form_set.append(form_three)
                form_result.append(form_three)
        for url in url_list :
            url_add = urlparse.urljoin(response.url,url)
            if '#' in url_add:
                url_add = url_add[:url_add.find('#')]
            if urlparse.urlparse(url_add).netloc == self.status_root.netloc and url_add not in UrlSpider.url_set:
                #signal.signal(signal.SIGALRM, self.myHandler)
                #signal.alarm(10)
                self.url_set.add(url_add) 
                url_result.append(url_add)
                yield scrapy.http.Request(url_add,callback=self.parse,dont_filter=True)
            '''
            status = urlparse.urlparse(url)
            if (status.netloc == '' and status.path != ''):
                #域名子目录或子网页
                url_add = urlparse.urljoin(self.root_url,url)
            elif (status.netloc == '' and status.query != ''):
                #域名子链接
                url_add = urlparse.urljoin(self.root_url,url)
            elif (status.netloc == self.status_root.netloc):
                #域名链接
                url_add = url
            else:
                url_add = ''
            if (urlparse.urlparse(url_add).netloc == self.status_root.netloc and url_add not in UrlSpider.url_set):
                #主域名相同并且为新增内链
                #signal.signal(signal.SIGALRM, self.myHandler)
                #signal.alarm(10)
                self.url_set.add(url_add)  
                url_result.append(url_add)
                yield scrapy.http.Request(url_add,callback=self.parse,dont_filter=True)
            '''
        item = NgItem()
        item['url'] = response.url
        item['form'] = form_result
        item['name'] = url_result
        yield item