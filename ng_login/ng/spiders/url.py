# -*- coding: utf-8 -*-
import scrapy
from ng.items import NgItem
import urlparse
import signal
import sys
from scrapy.selector import Selector
from py2neo import *
from ng.pipelines import graph_init
import re

class UrlSpider(scrapy.Spider):
    name = 'url'
    url_set = set()
    form_set = []

    def __init__(self, url=None, username=None,password=None,*args, **kwargs): 
        super(UrlSpider, self).__init__(*args, **kwargs) 
        self.start_urls = ['%s' % url]
        self.root_url = url
        self.username = username
        self.password = password
        self.status_root = urlparse.urlparse(url)        

    def myHandler(self, signum , frame):
        self.crawler.engine.close_spider(self, 'Spider exiting...')

    def start_requests(self):
        return [scrapy.http.Request(self.root_url,meta={'cookiejar': 1},callback=self.login)]
        #return [scrapy.http.Request(self.root_url,callback=self.login)]

    def login(self , response):
        user_list = {'user','usr','username','log'}
        pwd_list = {'pwd','password','user_pass'}
        form_list = response.xpath('//form').extract()
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
                    if name in user_list and value == '':
                        result[name] = self.username
                    if name in pwd_list and value == '':
                        result[name] = self.password
        return scrapy.FormRequest.from_response(response,url=action,meta={'cookiejar': response.meta['cookiejar']},formdata=result,callback=self.check,dont_filter=True)

    def check(self,response):
        self.meta = {'cookiejar': response.meta['cookiejar']}
        graph = graph_init()
        matcher = NodeMatcher(graph)
        node0 = matcher.match('url',name=self.root_url).first()
        if node0 is None:
            node0 = Node('url',name=self.root_url)
            node0['login_url'] = '1'
            node0['login_username_1'] = self.username
            graph.create(node0)
        if re.search('window\.location\.href',response.text):
            href_url = re.findall("\<script\>(.*?)href(.*?)\=(.*?)\'(.*?)\'\<\/script\>",response.text)[0][3]
            manage_url = urlparse.urljoin(response.url,href_url)
            return scrapy.http.Request(manage_url,meta=self.meta,callback=self.check,dont_filter=True)
        node1 = matcher.match('url',name=response.url).first()
        if node1 is None:
            node1 = Node('url',name=response.url)
            node1['username'] = self.username
            graph.create(node1)
        node0_know_node1 = Relationship(node0,'next',node1)
        graph.create(node0_know_node1)
        #self.meta = {'cookiejar': response.meta['cookiejar']}
        #yield scrapy.http.Request('http://127.0.0.1/DVWA/index.php',meta=self.meta,dont_filter=True) 
        return self.parse(response)

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
            try:
                action = form_selector.xpath('//form/@action').extract()[0] 
            except:
                continue
            if urlparse.urlparse(action).netloc == '' :#and urlparse.urlparse(action).path == '':
                action = urlparse.urljoin(response.url,action)
                # '#'
                #ParseResult(scheme='', netloc='', path=u'', params='', query='', fragment=u'') 
                #action = urlparse.urljoin(self.root_url,action) 
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
            if urlparse.urlparse(url_add).netloc == self.status_root.netloc and url_add not in UrlSpider.url_set and 'logout' not in url_add:
                #signal.signal(signal.SIGALRM, self.myHandler)
                #signal.alarm(10)
                self.url_set.add(url_add) 
                url_result.append(url_add)
                yield scrapy.http.Request(url_add,meta=self.meta,callback=self.parse,dont_filter=True)
            '''
            status = urlparse.urlparse(url)
            if (status.netloc == '' and status.path != ''):
                #域名子目录或子网页
                url_add = urlparse.urljoin(response.url,url)
            elif (status.netloc == '' and status.query != ''):
                #域名子链接
                url_add = urlparse.urljoin(response.url,url)
            elif (status.netloc == self.status_root.netloc):
                #域名链接
                url_add = url
            else:
                url_add = ''
            if (urlparse.urlparse(url_add).netloc == self.status_root.netloc and url_add not in UrlSpider.url_set):
                #主域名相同并且为新增内链
                #signal.signal(signal.SIGALRM, self.myHandler)
                #signal.alarm(10)
                if 'logout' in url_add:
                    break
                self.url_set.add(url_add) 
                url_result.append(url_add)
                yield scrapy.http.Request(url_add,meta=self.meta,callback=self.parse,dont_filter=True)
            '''
        item = NgItem()
        item['url'] = response.url
        item['form'] = form_result
        item['name'] = url_result
        item['username'] = self.username
        yield item

        

