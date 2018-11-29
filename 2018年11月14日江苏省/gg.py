#!/usr/bin/env python
#coding=utf-8

import time
import datetime
import re
import json
import requests
import time
import redis
import sys
from urlparse import urljoin
from db import DB
reload (sys)
import copy
import MySQLdb
sys.setdefaultencoding ("utf-8")
import htmlparser
from PIL import Image
def handle_post(post):
    post = copy.deepcopy(post)
    for k,v in post.iteritems():
        print k,v
        if isinstance(v, unicode):
            v = v.encode("utf8")
        if not isinstance(v,str) and not isinstance(v, int) and not isinstance(v, float):
            v = json.dumps(v)
        try:v = MySQLdb.escape_string(v)
        except:pass
        post.update({k:v})
    return post
db = DB ().create ('mysql://zhxg:ZHxg2017!@192.168.1.19:3306/sjk')
table = "list_info"
result1 = "list_model_filter"
urls = db.table(table).where('''siteName = "江苏省公共资源交易网"''').find()
dict_page_info = [url for url in urls if url is not None]
print "********-->", len (dict_page_info)
for str_urls in dict_page_info:
    dict_post = str_urls
    # print isinstance(dict_post,dict)
    # dict_post = json.loads(dict_post)
    # for k,v in dict_post.items():
    #     print k,v
    # dd = dict_post.get("detailUrl")

    dict_post["tf"]="1"
    dict_post["irepeat"]="1"
    dict_post["service"]="勘察设计"
    dict_post["industry"]="industry"

    dic = handle_post (dict_post)
    try:
        db.table (result1).add (dic)
    except Exception as e:
        print e
    # for k,v in dict_post.items():
    #     print k,v
    # detailUrl = dict_post.get ("detailUrl")

if __name__ == "__main__":
    pass