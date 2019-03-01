# -*- coding:utf-8 -*-
# _author = xupeng
# 采集的列表页，得到的结果为链接，标题，时间，地区
import spider
import setting
import htmlparser
import redis
import base64
import json
import math
import time
import re
import datetime
import urllib
import random
from urlparse import urljoin
import uuid
from db import DB
import MySQLdb
import sys
import requests
reload(sys)
sys.setdefaultencoding("utf-8")
import copy


class MySpider(spider.Spider):
    def __init__(self,
                 proxy_enable=False,
                 proxy_max_num=setting.PROXY_MAX_NUM,
                 timeout=setting.HTTP_TIMEOUT,
                 cmd_args=None):
        spider.Spider.__init__(self, proxy_enable, proxy_max_num, timeout=timeout, cmd_args=cmd_args)

        # 网站名称
        self.siteName = "江苏省公共资源交易网"
        # 类别码，01新闻、02论坛、03博客、04微博 05平媒 06微信  07 视频、99搜索引擎
        self.info_flag = "99"

        # 入口地址列表
        # self.start_urls = ["http://www.bidcenter.com.cn/viplist-1.html"]
        self.start_urls = ["http://jsggzy.jszwfw.gov.cn"]
        self.encoding = 'UTF-8'
        self.site_domain = 'jsggzy.jszwfw.gov.cn'
        self.dedup_uri = None
        self.timeout = 50
        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            # 'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            # 'Content-Length': '482',
            # 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            # 'Cookie': 'Hm_lvt_f7811e67b48a98d4be5d826f169a8075=1541662109,1542003546,1542078731; JSESSIONID=CB7535F288B576CAD7CFC351DDE08F35; Hm_lpvt_f7811e67b48a98d4be5d826f169a8075=1542086824',
            # 'Cookie': 'JSESSIONID=208CF281991660E236AC424937BC1BDB; ',
            # 'DNT': '1',
            # 'Host': 'jsggzy.jszwfw.gov.cn',
            # 'Origin': 'http://jsggzy.jszwfw.gov.cn',
            # 'Referer': 'http://jsggzy.jszwfw.gov.cn/jyxx/tradeInfonew.html',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36',
            # 'X-Requested-With': 'XMLHttpRequest',
            # "Content-Type":"application/x-www-form-urlencoded",

            # "Referer":"https://www.bidcenter.com.cn",
            # 'Cookie': 'ASP.NET_SessionId=edvtzkuc3fir5uo0dgd33pwl; UM_distinctid=166e2d98409596-08af12546c38b9-12656e4a-1fa400-166e2d9840a47e; CNZZDATA888048=cnzz_eid%3D758459646-1541404197-%26ntime%3D1541404197; Hm_lvt_9954aa2d605277c3e24cb76809e2f856=1541404198; Hm_lpvt_9954aa2d605277c3e24cb76809e2f856=1541404198',

        }
        # self.proxy_enable = "http://spider-ip-sync.istarshine.net.cn/proxy_100ms.txt"
        # #self.proxy_url = 'http://spider-ip-sync.istarshine.net.cn/proxy_100ms.txt'
        self.request_headers = {'headers': self.headers}

        self.conn_config = redis.StrictRedis.from_url ('redis://192.168.1.34/1')
        redis_ip = self.conn_config.get("redis_ip")
        redis_db = self.conn_config.get ("redis_db")
        mysql_ip = self.conn_config.get("mysql_ip")
        mysql_databases = self.conn_config.get ("mysql_databases")
        mysql_username = self.conn_config.get("mysql_username")
        mysql_password = self.conn_config.get ("mysql_password")
        mysql_list_info = self.conn_config.get ("mysql_list_info")
        try:
            self.conn = redis.StrictRedis.from_url ('redis://{0}/{1}'.format(redis_ip,redis_db))
        except:
            self.conn = None
        # self.db = DB ().create ('mysql://zhxg:ZHxg2017!@192.168.20.247:3306/hbdx')
        self.db = DB ().create ('mysql://{0}:{1}@{2}:3306/{3}'.format(mysql_username,mysql_password,mysql_ip,mysql_databases))
        # self.db = DB ().create ('mysql://root:1234@localhost:3306/sjk')
        self.table = mysql_list_info

    def get_start_urls(self, data=None):
        '''
        返回start_urls
        '''

        return self.start_urls

    def parse(self, response, url):
        equals = ['003001008', '003001007', '003001001', '003002001', '003002003', '003002004', '003003001',
                  '003003003', '003003004', '003004002', '003004003', '003004006']
        citys = ['省级', '南京市', '无锡市', '徐州市', '常州市', '苏州市', '南通市', '连云港市', '淮安市', '盐城市', '扬州市', '镇江市', '泰州市', '宿迁市']
        for city in citys:
            for equal in equals:
                for pn in range(0,40,20):
                    data1 = {"token": "",
                             "pn": pn,
                             "rn": "15",
                             "sdt": "",
                             "edt": "",
                             "wd": "",
                             "inc_wd": "",
                             "exc_wd": "",
                             "fields": "title",
                             "cnum": "001",
                             "sort": "{\"infodatepx\":\"0\"}",
                             "ssort": "title",
                             "cl": 200,
                             "terminal": "",
                             "condition": [
                                 {"fieldName": "categorynum", "isLike": True, "likeType": 2, "equal": equal},
                                 {"fieldName": "fieldvalue", "isLike": True, "likeType": 2, "equal": city}
                             ],
                             "time": None,
                             "highlights": "title", "statistics": None, "unionCondition": None, "accuracy": "", "noParticiple": "0",
                             "searchRange": None, "isBusiness": "1"}
                    url = 'http://jsggzy.jszwfw.gov.cn/inteligentsearch/rest/inteligentSearch/getFullTextData'
                    response = requests.post(url=url, json=data1)
                    dates = re.findall('"infodateformat":"(.*?)"', response.text)
                    titles = re.findall('"title":"(.*?)"', response.text)
                    ids = re.findall('"categorynum":"(.*?)"', response.text)[1:]
                    infoids = re.findall('"infoid":"(.*?)"', response.text)

                    for id, infoid, date,title in zip(ids, infoids, dates,titles):
                        date = date.replace("-","")
                        link = 'http://jsggzy.jszwfw.gov.cn/jyxx/' + id[:6] + "/" + id + "/" + date + "/" + infoid + ".html"
                        if id == "003001008":
                            tag = "中标公告"
                        elif id == "003001007":
                            tag = "候选人公告"
                        elif id == "003001001":
                            tag = "招标公告"
                        elif id == "003002001":
                            tag = "招标公告"
                        elif id == "003002003":
                            tag = "候选人公告"
                        elif id == "003002004":
                            tag = "中标公告"
                        elif id == "003003001":
                            tag = "招标公告"
                        elif id == "003003003":
                            tag = "候选人公告"
                        elif id == "003003004":
                            tag = "中标公告"
                        elif id == "003004002":
                            tag = "招标公告"
                        elif id == "003004003":
                            tag = "更正公告"
                        elif id == "003004006":
                            tag = "中标公告"
                        else:
                            tag = "招标公告"
                        link = str(link)
                        if self.getdumps(link):
                            continue
                        uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, link)) + str(uuid.uuid3(uuid.NAMESPACE_DNS, link))
                        ctime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        service = ''
                        industry = ""
                        post = {
                            "uuid": uid,  # md5
                            "detailUrl": link,  # url
                            "name": title,  # 标题
                            "location": "江苏省",  # 地区
                            "publicTime": date,  # 公布时间
                            "tag": tag,  # 标签
                            "site": self.site_domain,
                            "siteName": self.siteName,
                            "ctime": ctime,
                            "industry": industry,
                            "service": service,
                        }
                        dic = self.handle_post(post)
                        try:
                            self.db.table(self.table).add(dic)
                        except Exception as e:
                            print e



    def parse_detail_page(self, response=None, url=None):

        return

    def getdumps(self, url):
        if self.conn.sismember("dumps:jsggzy", url):
            return True  # 在里面
        else:
            print "入redis：去重库"
            self.conn.sadd("dumps:jsggzy", url)
            return False

    def handle_post(self, post):
        post = copy.deepcopy(post)
        for k, v in post.iteritems():
            print k, v
            if isinstance(v, unicode):
                v = v.encode("utf8")
            if not isinstance(v, str) and not isinstance(v, int) and not isinstance(v, float):
                v = json.dumps(v)
            try:
                v = MySQLdb.escape_string(v)
            except:
                pass
            post.update({k: v})
        return post


if __name__ == '__main__':
    spider = MySpider()
    spider.proxy_enable = True
    spider.init_dedup()
    spider.init_downloader()

    # ------------ parse_detail_page() ----------
    url = "http://ggzy.hefei.gov.cn/jyxx/002001/002001001/1.html"
    resp = spider.download(url)
    res = spider.parse_detail_page(resp, url)

