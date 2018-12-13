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
        self.siteName = "辽宁建设工程信息网"
        # 类别码，01新闻、02论坛、03博客、04微博 05平媒 06微信  07 视频、99搜索引擎
        self.info_flag = "99"

        # 入口地址列表
        # self.start_urls = ["http://www.bidcenter.com.cn/viplist-1.html"]
        self.start_urls = ["http://www.lnzb.cn"]
        self.encoding = 'utf-8'
        self.site_domain = 'lnzb.cn'
        self.dedup_uri = None
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
            "Connection": "keep-alive",
            # "Cookie": "_gscu_1811078948=41663282vx6ent53; ASP.NET_SessionId=x01pkg455lrliaiky4l3av45; _gscbrs_1811078948=1; _gscs_1811078948=t42005267lfkkmo53|pv:3; cookies=89314150",
            # bidguid=96984f59-dcbf-491f-9bab-a8500ea4f12d; UM_distinctid=16492ad9f0ba4-0c0a2c42949499-444a002e-1fa400-16492ad9f0c2aa; _uab_collina=153146928107553947905014; _umdata=BA335E4DD2FD504F1EDA57F02CFE1964FF30093E1A99816EA3422927037FEEE27E6061217D847EA9CD43AD3E795C914CF0452994C1509D8EB7661DBFB2FCDD56; isshowtcc=isshowtcc; BIDCTER_USERNAME=UserName=jingyingbu666; keywords=%u601D%u79D1; keywords==%e6%80%9d%e7%a7%91; CNZZDATA888048=cnzz_eid%3D1104734771-1531464092-%26ntime%3D1531696377; Hm_lvt_9954aa2d605277c3e24cb76809e2f856=1531469210,1531700960; Hm_lpvt_9954aa2d605277c3e24cb76809e2f856=1531701399; aspcn=id=1277449&name=jingyingbu666&vip=3&company=%e8%8b%8f%e4%ba%a4%e7%a7%91%e9%9b%86%e5%9b%a2%e8%82%a1%e4%bb%bd%e6%9c%89%e9%99%90%e5%85%ac%e5%8f%b8&lianxiren=%e6%b8%b8%e7%8e%89%e7%9f%b3&tel=025-86577542&email=yys@jsti.com&diqu=&Token=65D51EA060022C3EFFD2BE6B4C79852284FE102150132499D822DB4759BA5217232FAA3570FA85C59F0D4B7BA2A98C4B; PASSKEY=Token=65D51EA060022C3EFFD2BE6B4C79852284FE102150132499D822DB4759BA5217232FAA3570FA85C59F0D4B7BA2A98C4B',
            # "Host": "www.fjggzyjy.cn",
            "Upgrade-Insecure-Requests": "1",
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
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001001&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001002&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001003&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001004&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001005&QuYu=0',
            # 工程建设招标公告

            'http://www.lnzb.cn/lnzbtb/showinfo/zbgs.aspx?categoryNum=003002001&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgs.aspx?categoryNum=003002002&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgs.aspx?categoryNum=003002003&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgs.aspx?categoryNum=003002004&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgs.aspx?categoryNum=003002005&QuYu=0',
            # 工程建设中标候选人公示

            'http://www.lnzb.cn/lnzbtb/showinfo/zbjg.aspx?categoryNum=003003001&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbjg.aspx?categoryNum=003003002&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbjg.aspx?categoryNum=003003003&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbjg.aspx?categoryNum=003003004&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbjg.aspx?categoryNum=003003005&QuYu=0',
            # 工程建设中标公告

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

        zhaobgg = [
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001001&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001002&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001003&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001004&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001005&QuYu=0',
        ]
        hxrzs = [
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgs.aspx?categoryNum=003002001&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgs.aspx?categoryNum=003002002&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgs.aspx?categoryNum=003002003&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgs.aspx?categoryNum=003002004&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbgs.aspx?categoryNum=003002005&QuYu=0',
        ]
        zhongbgg = [
            'http://www.lnzb.cn/lnzbtb/showinfo/zbjg.aspx?categoryNum=003003001&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbjg.aspx?categoryNum=003003002&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbjg.aspx?categoryNum=003003003&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbjg.aspx?categoryNum=003003004&QuYu=0',
            'http://www.lnzb.cn/lnzbtb/showinfo/zbjg.aspx?categoryNum=003003005&QuYu=0',
        ]
        if from_tag_url in zhaobgg:
            tag = "招标公告"
        elif from_tag_url in hxrzs:
            tag = "候选人公示"
        elif from_tag_url in zhongbgg:
            tag = "中标公告"
        else:
            tag = "招标公告"
        text = re.findall("\['(.*?)','(.*?)','.*?','(.*?)',", unicode_html_body, re.S)
        for i in text:
            title = i[0]
            link = i[1]
            date = i[2]
            date = str(date).replace("-", "")

#         titles = data.xpathall('//a[@class="btn btn-default article-list-single"]/@title')
#         links = data.xpathall('//a[@class="btn btn-default article-list-single"]/@href')
#         dates = data.xpathall('//span[@class="article-list-date"]/text()')


            link = "http://www.lnzb.cn/lnzbtb/infodetail/Default.aspx?infoid="+link

            link = str(link)
            if self.getdumps(link):
                continue
            uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, link)) + str(uuid.uuid3(uuid.NAMESPACE_DNS, link))
            ctime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            location = "辽宁省"
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

            # str_post = json.dumps (post)

        return

    def getdumps(self, url):
        if self.conn.sismember("dumps:lnzb", url):
            return True  # 在里面
        else:
            print "入redis：去重库"
            self.conn.sadd("dumps:lnzb", url)
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

    url = "http://www.lnzb.cn/lnzbtb/showinfo/zbgg.aspx?categoryNum=003001001&QuYu=0"
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
