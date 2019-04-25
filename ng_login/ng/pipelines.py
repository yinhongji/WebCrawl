# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import urlparse
from py2neo import *
def graph_init():
	graph =  Graph("http://127.0.0.1:7474",username="neo4j",password="123456")
	return graph

def graph_add(info , username):
	url , next_url_param = info[0] , info[1]
	#print url , next_url_param
	graph = graph_init()
	matcher = NodeMatcher(graph)
	node0 = matcher.match('url',name=url).first()
	if node0 is None:
		#若前节点不存在，创建前节点
		node0 = Node('url',name=url)
		node0['login_username_1'] = username
		graph.create(node0)
	else:
		query = """MATCH (n {name:'%s'}) SET n += {login_username_1:'%s'} RETURN n""" % (url,username)
		graph.run(query)

	if type(next_url_param) == list:
		#url三元组 [url,get/post,param]
		node1 = matcher.match('url',name=next_url_param[0]).first()
		if node1 is None:
			#若后节点不存在，创建后节点
			node1 = Node('url',name=next_url_param[0])
			node1['login_username_1'] = username
			graph.create(node1)
		else:
			query = """MATCH (n {name:'%s'}) SET n += {login_username_1:'%s'} RETURN n""" % (next_url_param[0],username)
			graph.run(query)

		if node0['name'] != node1['name']:
			node0_know_node1 = Relationship(node0,'next',node1)
			graph.create(node0_know_node1)

		if next_url_param[2]:
			param_node = Node('param',url_name=next_url_param[0])
			param_node['web_type'] = next_url_param[1]
			#param_node['login_username'] = username
			for x in next_url_param[2].keys():
				param_node[x] = next_url_param[2][x]
			graph.create(param_node)
			node1_know_param_node = Relationship(node1,'param',param_node)
			graph.create(node1_know_param_node)
	else:
		#url 
		node1 = matcher.match('url',name=next_url_param).first()
		if node1 is None:
			#若后节点不存在，创建后节点
			node1 = Node('url',name=next_url_param)
			node1['login_username_1'] = username
			graph.create(node1)
		else:
			query = """MATCH (n {name:'%s'}) SET n += {login_username_1:'%s'} RETURN n""" % (next_url_param,username)
			graph.run(query)

		if node0['name'] != node1['name']:
			node0_know_node1 = Relationship(node0,'next',node1)
			graph.create(node0_know_node1)

def solve(name,tag):
	result = []
	if tag == 'form':
		for x in name:
			result.append(x)
	elif tag == 'name':
		for x in name:
			'''
			if len(x.split('?')) <= 1 :
				url = x 
				param_list = ''
			else:
				url , param = x.split('?')[0] , x.split('?')[1]
				param = param.split('&')
				param_list = {}
				for y in param:
					key , value = y.split('=')[0] , y.split('=')[1]
					param_list[key] = value
			add = [url , 'get' , param_list]
			result.append(add)
			'''
			result.append(x)
	return result
class NgPipeline(object):
    def process_item(self, item, spider):
    	result , result_form , result_name = [] , [] , []
        if item['form']:
        	result_form = solve(item['form'],'form')
        if item['name']:
        	result_name = solve(item['name'],'name')
        result = result_form + result_name
        for x in result:
        	info = (item['url'] , x)
        	username = item['username']
        	#print item['url'] , x
        	graph_add(info , username)
