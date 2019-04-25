#coding:utf-8
from py2neo import *
import subprocess
import time
import re
url = 'http://127.0.0.1/101html/index.php'
login_url = 'http://127.0.0.1:9999/wp-login.php'
username = 'admin'
password = 'admin'
def graph_init():
	graph =  Graph("http://127.0.0.1:7474",username="neo4j",password="123456")
	graph.delete_all()
def run_scrapy():
	cmd = 'cd ng && scrapy crawl url -a url=%s' % url
	p=subprocess.call(cmd,shell=True)
def run_scrapy_login():
	cmd = 'cd ng_login && scrapy crawl url -a url=%s -a username=%s -a password=%s ' % (login_url,username,password)
	p=subprocess.call(cmd,shell=True)
def main():
	graph_init()
	run_scrapy()
	#time.sleep(2)
	#run_scrapy_login()
main()

'''
def get_node(result):
	past_node = re.findall('name\: \'(.*?)\'',result)
	print past_node
graph =  Graph("http://127.0.0.1:7474",username="neo4j",password="123456")

attack_url = 'http://127.0.0.1/101html/index.php?c=admin&a=save_content'
shortest_query = """
MATCH (p1:url {name:'%s'}),(p2:url{name:'%s'}),
p=shortestpath((p1)-[*..10]-(p2))
RETURN nodes(p)
""" 
shortest_query_url = shortest_query % (url,attack_url)
result = graph.run(shortest_query_url)
past_node_list = get_node(str(list(result)[0]))

shortest_query_login = shortest_query % (login_url,attack_url)
result = graph.run(shortest_query_login)
past_node_list_login = get_node(str(list(result)[0]))
'''
