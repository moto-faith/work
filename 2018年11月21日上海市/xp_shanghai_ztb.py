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
import ssl
import copy

ssl._create_default_https_context = ssl._create_unverified_context


class MySpider(spider.Spider):
    def __init__(self,
                 proxy_enable=False,
                 proxy_max_num=setting.PROXY_MAX_NUM,
                 timeout=setting.HTTP_TIMEOUT,
                 cmd_args=None):
        spider.Spider.__init__(self, proxy_enable, proxy_max_num, timeout=timeout, cmd_args=cmd_args)

        # 网站名称
        self.siteName = "上海市建设工程交易服务中心"
        # 类别码，01新闻、02论坛、03博客、04微博 05平媒 06微信  07 视频、99搜索引擎
        self.info_flag = "99"

        # 入口地址列表
        # self.start_urls = ["http://www.bidcenter.com.cn/viplist-1.html"]
        self.start_urls = ["http://www.shcpe.cn"]
        self.encoding = 'utf-8'
        self.site_domain = 'shcpe.cn'
        self.dedup_uri = None
        self.headers = {
            # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            # "Accept-Encoding": "gzip, deflate, br",
            # "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
            # "Connection": "keep-alive",
            # "Cookie": "_gscu_1811078948=41663282vx6ent53; ASP.NET_SessionId=x01pkg455lrliaiky4l3av45; _gscbrs_1811078948=1; _gscs_1811078948=t42005267lfkkmo53|pv:3; cookies=89314150",
            # bidguid=96984f59-dcbf-491f-9bab-a8500ea4f12d; UM_distinctid=16492ad9f0ba4-0c0a2c42949499-444a002e-1fa400-16492ad9f0c2aa; _uab_collina=153146928107553947905014; _umdata=BA335E4DD2FD504F1EDA57F02CFE1964FF30093E1A99816EA3422927037FEEE27E6061217D847EA9CD43AD3E795C914CF0452994C1509D8EB7661DBFB2FCDD56; isshowtcc=isshowtcc; BIDCTER_USERNAME=UserName=jingyingbu666; keywords=%u601D%u79D1; keywords==%e6%80%9d%e7%a7%91; CNZZDATA888048=cnzz_eid%3D1104734771-1531464092-%26ntime%3D1531696377; Hm_lvt_9954aa2d605277c3e24cb76809e2f856=1531469210,1531700960; Hm_lpvt_9954aa2d605277c3e24cb76809e2f856=1531701399; aspcn=id=1277449&name=jingyingbu666&vip=3&company=%e8%8b%8f%e4%ba%a4%e7%a7%91%e9%9b%86%e5%9b%a2%e8%82%a1%e4%bb%bd%e6%9c%89%e9%99%90%e5%85%ac%e5%8f%b8&lianxiren=%e6%b8%b8%e7%8e%89%e7%9f%b3&tel=025-86577542&email=yys@jsti.com&diqu=&Token=65D51EA060022C3EFFD2BE6B4C79852284FE102150132499D822DB4759BA5217232FAA3570FA85C59F0D4B7BA2A98C4B; PASSKEY=Token=65D51EA060022C3EFFD2BE6B4C79852284FE102150132499D822DB4759BA5217232FAA3570FA85C59F0D4B7BA2A98C4B',
            # "Host": "www.fjggzyjy.cn",
            # "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",

            # "Content-Type":"application/x-www-form-urlencoded",

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
            'https://www.ciac.sh.cn/NetInterBidweb/GKTB/SgfbZbxx.aspx',
            # 招标公告
            # 'https://www.ciac.sh.cn/XmZtbbaWeb/gsqk/ZbjgGkList.aspx',
            # 中标公告
        ]

        #
        # for i in range(102, 114):
        #     url_request ={
        #         "url":"https://www.ciac.sh.cn/XmZtbbaWeb/gsqk/ZbjgGkList.aspx",
        #         "method":"post",
        #         "data" :{
        #              '__EVENTTARGET': 'gvZbjgGkList$ctl{}$lbXmmc'.format(str(i)[1:]),
        #              '__VIEWSTATE': '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',
        #              '__VIEWSTATEGENERATOR': 'DF0C86B1',
        #              '__EVENTVALIDATION': '/wEdACKvsdnqCxdGkTZhW1x4UsXhYFVDskWoBzzIrjzhjMGivogI9Z3UT/Np2jYuM7RA6V0ao6o3sRSHcU5sf0XALLa6A18+64hmj2eWnRPDW4+ryCcBMyY+qjA1ILbkB2FsZTx9Crw1xhUrT0E3/kAmOFugSEbR4F4+APsGZUeEFoAWebqKz6BbAEmBmG4HqNVJizPICRVKEKSQGLkVVlwN8YDPY+hv0FGmXYLYLs870l7gTJ3AHD63+4oeB+Ybs0yx6bezf6ezZYHW9PnV8gr0GSwxqJFi/ODgwBuBWFR1hNYkWI7U3Vc0WZ+wxclqyPFfzmPkILkKejWkjx6dQ/Apk3HyYDdyYMdmueZO9G+32xcfonJVtGz6Fn5fSb329wpJcKDym1WM+tuQFAQhY3+AbRLTnALvOh+tWKGkJjMWZUySvEJ5fFYhh0kwIhiTKrHeHVHCZiumaro7TsTworhjqiSotlbCk61yHgkq1hzr/l2oujEMD0YtxKUu81vRTJLdWw8gDeS2CPxC3zNevwye2lvOJttITsL3ldBFABFwpoeyWaEqX98l6odgwQMGJM3ORvhHHVIInUrzz1CVM2aBrvIe4wo8r+UDy1cfCTiPR1Z81EBIoIXPm1wvnetu0tVB9bUXetMwQsQrenIdg26mFm4+sSzuIKWEz3J7wCt2CYfbaC2BT6o+AJsIt7rIqeg88jKCWw8e2RW4sSXaZ41WgCOvmMTr0lwn76sY3aZVuXZYPDhPA+k=',
        #          },
        #     },
        return (url_list, None, None)


    def parse_detail_page(self, response=None, url=None):
        try:
            response.encoding = self.encoding
            unicode_html_body = response.text
            data = htmlparser.Parser(unicode_html_body)
        except Exception, e:
            return []
        from_tag_url = response.url
        # print unicode_html_body
        # titles = re.findall('target="_blank" title="(.*?)"', unicode_html_body, re.S)
        # links = re.findall('href="(.*?)" target="_blank"',unicode_html_body,re.S)
        # dates = re.findall('<span class="date">(.*?)</span>',unicode_html_body,re.S)

        tag = "招标公告"
        dates = re.findall('(\d{4}/\d{2}/\d{2})', unicode_html_body, re.S)
        ids = set(re.findall("openWindow\('(.*?)'", unicode_html_body, re.S))
        titles = re.findall('class="borderDealwith">(.*?)<', unicode_html_body, re.S)
        for date, id, title in zip(dates, ids, titles):
            title = str(title).strip()
            link = 'https://www.ciac.sh.cn/NetInterBidweb/GKTB/DefaultV2011.aspx?gkzbXh={}'.format(id)
            date = str(date).replace("/", "")
            if self.getdumps(link):
                continue
            link = str(link)
            uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, link)) + str(uuid.uuid3(uuid.NAMESPACE_DNS, link))
            ctime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            location = "上海市"
            service = ''
            industry = ""
            post = {
                "uuid": uid,  # md5
                "detailUrl": link,  # url
                "name": title,  # 标题
                "location": location,  # 地区
                "publicTime": date,  # 公布时间
                "tag": tag,  # 标签
                "site": self.site_domain,
                "siteName": self.siteName,
                "ctime": ctime,
                "industry": industry,
                "service": service

            }

            dic = self.handle_post(post)
            try:
                self.db.table(self.table).add(dic)
            except Exception as e:
                print e


        return

    def getdumps(self, url):
        if self.conn.sismember("dumps:shcpe", url):
            return True  # 在里面
        else:
            print "入redis：去重库"
            self.conn.sadd("dumps:shcpe", url)
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

    url = "https://www.ciac.sh.cn/NetInterBidweb/GKTB/SgfbZbxx.aspx"
    resp = spider.download(url)
    res = spider.parse_detail_page(resp, url)
    # for item in res:
    #     for k, v in item.iteritems():
    #         print k, v
    #         print "*"*30

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
