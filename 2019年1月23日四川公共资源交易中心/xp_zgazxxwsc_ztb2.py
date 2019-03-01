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
from db import DB
import MySQLdb
import uuid

import requests
import copy
import urllib3

class MySpider(spider.Spider):
    def __init__(self,
                 proxy_enable=False,
                 proxy_max_num=setting.PROXY_MAX_NUM,
                 timeout=setting.HTTP_TIMEOUT,
                 cmd_args=None):
        spider.Spider.__init__(self, proxy_enable, proxy_max_num, timeout=timeout, cmd_args=cmd_args)

        # 网站名称
        self.siteName = "四川公共资源交易中心"
        # 类别码，01新闻、02论坛、03博客、04微博 05平媒 06微信  07 视频、99搜索引擎
        self.info_flag = "99"

        # 入口地址列表
        # self.start_urls = ["http://www.bidcenter.com.cn/viplist-1.html"]
        self.start_urls = ["http://www.zgazxxw.com"]
        self.encoding = 'gb2312'
        self.site_domain = 'zgazxxw.com'
        self.dedup_uri = None
        self.headers = {
            # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            # 'Accept-Encoding': 'gzip, deflate',
            # 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            # 'Cache-Control': 'max-age=0',
            # 'Connection': 'keep-alive',
            # 'Cookie': 'UM_distinctid=1670593cdcc4f5-0800ff5ff60ef9-594d2a16-15f900-1670593cdce395; CNZZDATA1264557630=446493554-1541984678-%7C1541984678',
            # 'DNT': '1',
            # 'Host': 'www.scggzy.gov.cn',
            # 'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36',


            # "Referer":"https://www.bidcenter.com.cn",
            # 'Cookie': 'ASP.NET_SessionId=edvtzkuc3fir5uo0dgd33pwl; UM_distinctid=166e2d98409596-08af12546c38b9-12656e4a-1fa400-166e2d9840a47e; CNZZDATA888048=cnzz_eid%3D758459646-1541404197-%26ntime%3D1541404197; Hm_lvt_9954aa2d605277c3e24cb76809e2f856=1541404198; Hm_lpvt_9954aa2d605277c3e24cb76809e2f856=1541404198',

        }
        # self.proxy_enable = "http://spider-ip-sync.istarshine.net.cn/proxy_100ms.txt"
        #self.proxy_url = 'http://spider-ip-sync.istarshine.net.cn/proxy_100ms.txt'
        self.request_headers = {'headers': self.headers}
        self.conn_config = redis.StrictRedis.from_url ('redis://192.168.1.34/1')
        redis_ip = self.conn_config.get("redis_ip")
        redis_db = self.conn_config.get ("redis_db")
        mysql_ip = self.conn_config.get("mysql_ip")
        mysql_databases = self.conn_config.get ("mysql_databases")
        mysql_username = self.conn_config.get("mysql_username")
        mysql_password = self.conn_config.get ("mysql_password")
        mysql_list_info = self.conn_config.get ("mysql_table1")
        result1 = self.conn_config.get ("mysql_list_model_filter")
        base2 = self.conn_config.get ("mysql_detail_info")
        try:
            self.conn = redis.StrictRedis.from_url ('redis://{0}/{1}'.format(redis_ip,redis_db))
        except:
            self.url_db = None
        self.db = DB ().create ('mysql://{0}:{1}@{2}:3306/{3}'.format(mysql_username,mysql_password,mysql_ip,mysql_databases))
        self.table = mysql_list_info
        self.result1 = result1
        self.base2 = base2

        self.sess = requests.session()

        self.all= {}
    def get_start_urls(self, data=None):
        '''
        返回start_urls
        '''
        return self.start_urls

    def parse(self, response, url):
        '''
        抓取列表页下所有详情页的链接
        '''
        # pipe = self.url_db.pipeline()
        # for _ in xrange(self.limit):
        #     # pipe.rpoplpush(self.list,self.list)
        #     pipe.rpop(self.list)
        # try:
        #     urls = pipe.execute()
        # except:
        #     urls = []
        page_urls = []
        urls = self.db.table(self.result1).where('''tf = "1" and siteName = "四川公共资源交易中心"''').find()
        dict_page_info = [url for url in urls if url is not None]
        # print "********-->",len(dict_page_info)
        for str_urls in dict_page_info:
            # print "str_urls",str_urls

            # dict_post = json.loads(str_urls)
            dict_post =str_urls
            try:
                detailUrl = dict_post.get("detailUrl")
            except Exception as e:
                print e

            self.all[detailUrl] = dict_post
            page_urls.append(detailUrl)
        return (page_urls, None, None)

    def parse_detail_page(self, response=None, url=None):
        try:
            response.encoding = self.encoding
            unicode_html_body = response.text
            data = htmlparser.Parser (unicode_html_body)
        except Exception, e:
            return []

        detail_url = response.url
        dict_post = self.all.get(detail_url)
        ctime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print ctime

        if data:
            content_xmls = data.xpathall (
                '''//div[@class="list_content fl"]''')
            content_xml = ""
            for i in content_xmls:
                content_xml += i.data

            # 2招标（中标）内容
            contents = data.xpathall (
                '''//div[@class="list_content fl"]//text()''')  # 内容
            content = ''
            for i in contents:
                content += i.text ().strip () + " "
            if content=='':
                content = self.siteName

            content = self.makecontent (content)
            # 4采购人
            tender = self.getPurchasingPersonName (content, content_xml)
            # 中标人
            bidder = self.getPurchasingPerson (content, content_xml)
            # 价格
            price = self.getprice (content, content_xml)

            post = {
                "id":dict_post.get ("id"),
                "uuid":dict_post.get ("uuid") ,  # md5
                "detailUrl": detail_url,  # url
                "name": dict_post.get ("name"),  # 标题
                "location": dict_post.get ("location"),  # 地区
                "publicTime": dict_post.get ("publicTime"),  # 公布时间
                "tag": dict_post.get ("tag"),  # 标签
                "site": self.site_domain,#域名
                "siteName": self.siteName,#域名名稱
                "ctime": ctime,#采集時間
                "service":dict_post.get ("service"),
                "industry":dict_post.get ("industry"),
                "price":price,#價格
                "tender":tender,#招標人
                "bidder":bidder,#中標人

                "content":content,

            }

            dic = self.handle_post (post)
            try:
                self.db.table (self.base2).add (dic)
                y = {"tf": "0"}
                self.db.table (self.result1).where ('''uuid="{0}"'''.format (dict_post.get ("uuid"))).update (y)
            except Exception as e:
                print e

    def handle_post(self,post):
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



    def makecontent(self,content):
        # print "before:", content
        content = re.sub (" |\t|\n|\r|\r\n", "", content).strip ()
        content = content.replace (" ", "").strip ()
        content = ''.join (content.split (" "))
        # print "after", content
        return content

    def getPurchasingPersonName(self,content, content_xml):
        # 4采购人
        # 4采购人
        try:
            purchasing_person_name = re.findall("流出方代表&lt;/td&gt;&lt;td style=&quot;text-align:left;&quot; colspan=&quot;3&quot;&gt;(.*?)&lt;", content, re.M)[0]
        except:
            try:
                purchasing_person_name = re.findall("采购人：(.*?)地", content, re.M)[0]
            except:
                try:
                    purchasing_person_name = re.findall("采购人：(.*?)联", content, re.M)[0]
                except:
                    purchasing_person_name = ''
        if not purchasing_person_name:
            try:
                purchasing_person_name = re.findall("招标人：(.*?)地", content, re.M)[0]
            except:
                try:
                    purchasing_person_name = re.findall("招标人：(.*?)联", content, re.M)[0]
                except:
                    try:
                        purchasing_person_name = re.findall("招标人名称：(.*?)地", content, re.M)[0]
                    except:
                        purchasing_person_name = ''

        # print purchasing_person_name
        return purchasing_person_name

    def getPurchasingPerson(self,content, content_xml):
        try:
            purchasing_person_name = re.findall ("流入方代表&lt;/td&gt;&lt;td style=&quot;text-align:left;&quot;&gt;(.*?)&lt;", content, re.M)[0]

        except:
            try:
                purchasing_person_name = re.findall ("成交供应商(.*?)<", content_xml, re.M)[0]
            except:
                try:
                    purchasing_person_name = re.findall ("采购人(.*?)<", content_xml, re.M)[0]
                except:
                    purchasing_person_name = ''
        return purchasing_person_name.replace ("：", "").replace (":", "").strip ()

    def getprice(self,content, content_xml):
        try:
            purchasing_person_name = re.findall ("成交价&lt;/td&gt;&lt;td style=&quot;text-align:left;&quot; colspan=&quot;3&quot;&gt;(.*?)&lt;", content_xml, re.M)[0]
        except:
            try:
                purchasing_person_name = re.findall ("金额(.*?)<", content_xml, re.M)[0]
            except:
                try:
                    purchasing_person_name = re.findall ("中标价(.*?)中标", content, re.M)[0]
                except:
                    purchasing_person_name = ''

        return purchasing_person_name.replace ("：", "").replace (":", "").strip ()


if __name__ == '__main__':
    spider = MySpider()
    spider.proxy_enable = False
    spider.init_dedup()
    spider.init_downloader()
    # ------------ parse() ----------
    # print "开始登录"
    # url = "http://changde.hnsggzy.com/jygkjygg/452957.jhtml"
    # resp = spider.download(url)
    # res = spider.parse(resp, url)


    # ------------ parse_detail_page() ----------
    # url = "http://www.bidcenter.com.cn/zbpage-4-%E6%B1%9F%E8%8B%8F-1.html"
    # resp = spider.download(url)
    # res = spider.parse_detail_page(resp, url)
    # for item in res:
    #     for k, v in item.iteritems():
    #         print k, v

