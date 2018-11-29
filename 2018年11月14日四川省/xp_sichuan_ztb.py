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
        self.siteName = "四川省公共资源交易中心"
        # 类别码，01新闻、02论坛、03博客、04微博 05平媒 06微信  07 视频、99搜索引擎
        self.info_flag = "99"

        # 入口地址列表
        # self.start_urls = ["http://www.bidcenter.com.cn/viplist-1.html"]
        self.start_urls = ["http://www.scggzy.gov.cn"]
        self.encoding = 'utf-8'
        self.site_domain = 'scggzy.gov.cn'
        self.dedup_uri = None
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            # 'Cookie': 'UM_distinctid=1670593cdcc4f5-0800ff5ff60ef9-594d2a16-15f900-1670593cdce395; CNZZDATA1264557630=446493554-1541984678-%7C1541984678',
            # 'DNT': '1',
            # 'Host': 'www.scggzy.gov.cn',
            # 'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36',
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
        # try:
        #     # response.encoding = self.encoding
        #     # unicode_html_body = response.text
        #     # data = htmlparser.Parser(unicode_html_body)
        # except Exception, e:
        #     return ([], None, None)
        url_list = [
            'http://www.scggzy.gov.cn/Info/GetInfoListNew?times=4&page=1&parm=1541986925633',
            # 'http://www.scggzy.gov.cn/Info/GetInfoListNew?times=4&page=2&parm=1541986925633',
        ]

        return (url_list, None, None)

    def parse_detail_page(self, response=None, url=None):
        try:
            response.encoding = self.encoding
            unicode_html_body = response.text
            data = htmlparser.Parser(unicode_html_body)
        except Exception, e:
            return []
        from_tag_url = response.url
        print from_tag_url
        # print unicode_html_body

        json_list = json.loads(unicode_html_body)["data"]
        titles = re.findall('"Title":"(.*?)"', json_list)
        links = re.findall('"Link":"(.*?)"', json_list)
        dates = re.findall('"CreateDateStr":"(.*?)"', json_list)
        tags = re.findall('"TableName":"(.*?)"', json_list)
        citys = re.findall('"username":"(.*?)"', json_list)

        for title,link,date,tag,city in zip(titles,links,dates,tags,citys):
            link = 'http://www.scggzy.gov.cn'+str(link)
            if self.getdumps(link):
                continue
            date = str(date).replace("-","")
            uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, link)) + str(uuid.uuid3(uuid.NAMESPACE_DNS, link))
            ctime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            service = ''
            industry = ""
            post = {
                "uuid": uid,  # md5
                "detailUrl": link,  # url
                "name": title,  # 标题
                "location": "四川省",  # 地区
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

            # str_post = json.dumps (post)

        return

    def getdumps(self, url):
        if self.conn.sismember("dumps:scggzy", url):
            return True  # 在里面
        else:
            print "入redis：去重库"
            self.conn.sadd("dumps:scggzy", url)
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
    spider.proxy_enable = False
    spider.init_dedup()
    spider.init_downloader()

    # ------------ parse_detail_page() ----------

    url = "http://www.scggzy.gov.cn/Info/GetInfoListNew?times=4&page=1&parm=1541986925633"
    resp = spider.download(url)
    res = spider.parse_detail_page(resp,url)
    # for item in res:
    #     for k, v in item.iteritems():
    #         print k, v

    # ------------ parse_detail_page() ----------
    # "https://www.bidcenter.com.cn/zbpage-1-1.html",  # 招标公告
    # "https://www.bidcenter.com.cn/zbpage-4-1.html",  # 中标公告
    # "https://www.bidcenter.com.cn/zbpage-6-1.html",  # 招标变更
    # for i in xrange(10,100):
    #     url = "https://www.bidcenter.com.cn/zbpage-6-{0}.html".format(i)
    #     resp = spider.download(url)
    #     res = spider.parse_detail_page(resp, url)
    #     # for item in res:
    #     #     for k, v in item.iteritems():
    #     #         print k, v
    #     time.sleep(5)

    # ------------ parse_detail_page() ----------
    # while 1:
    #     sli = [
    #             "https://www.bidcenter.com.cn/zbpage-1-1.html",  # 招标公告
    #             "https://www.bidcenter.com.cn/zbpage-4-1.html",  # 中标公告
    #             "https://www.bidcenter.com.cn/zbpage-6-1.html",  # 招标变更
    #         ]
    #     for url in sli:
    #         resp = spider.download(url)
    #         res = spider.parse_detail_page(resp, url)
    #         # for item in res:
    #         #     for k, v in item.iteritems():
    #         #         print k, v
    #         time.sleep(5)
    #     time.sleep(3)
