# -*- coding:utf-8 -*-
# _author = xupeng
# 采集的列表页，得到的结果为链接，标题，时间，地区
import requests
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
import copy


class MySpider(spider.Spider):
    def __init__(self,
                 proxy_enable=False,
                 proxy_max_num=setting.PROXY_MAX_NUM,
                 timeout=setting.HTTP_TIMEOUT,
                 cmd_args=None):
        spider.Spider.__init__(self, proxy_enable, proxy_max_num, timeout=timeout, cmd_args=cmd_args)

        # 网站名称
        self.siteName = "甘肃省招标中心"
        # 类别码，01新闻、02论坛、03博客、04微博 05平媒 06微信  07 视频、99搜索引擎
        self.info_flag = "99"

        # 入口地址列表
        # self.start_urls = ["http://www.bidcenter.com.cn/viplist-1.html"]
        self.start_urls = ["http://ggzyjy.gansu.gov.cn"]
        self.encoding = 'utf-8'
        self.site_domain = 'ggzyjy.gansu.gov.cn'
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
        areas = [620100,620200,620300,620400,620500,620600,620700,620800,620900,621000,621100,621200,622900,623000,620001]
        projecttypes = ['A','D']
        for projecttype in projecttypes:
            for area in areas:
                postData = {
                    "pageNo": "0",
                    "pageSize": "",
                    "area":area,
                    "projecttype":projecttype,
                    "prjpropertynewA": "A",
                    "prjpropertynewD": "D",
                    "prjpropertynewC": "C",
                    "prjpropertynewB": "B",
                    "prjpropertynewE": "E",
                    "prjpropertynewZ": "Z",
                    "projectname": "",

                }
                response = requests.post('http://ggzyjy.gansu.gov.cn/f/province/annogoods/getAnnoList',data=postData).text
                data = htmlparser.Parser(response)
                li_content = data.xpathall('''//dd''')
                for item in li_content:
                    title = item.xpath('''//a/text()''').text().strip()
                    link = item.xpath('''//a/@href''').text().strip()

                    #请求包含正文的网址
                    tradingCode = re.findall('cityTenderProject/(.*?)/',link)[0]
                    if projecttype=='A':
                        tableName = ''
                    else:
                        tableName = re.findall('&table=(.*)',link)[0]
                    postdata1 = {
                        "tradingCode":tradingCode,
                        "index": "0",
                        "projectType":projecttype,
                        "tableName":tableName
                    }
                    detailResponse = requests.post('http://ggzyjy.gansu.gov.cn/f/cityTenderProject/flowpage',data=postdata1).text
                    detaildata = htmlparser.Parser(detailResponse)
                    detaillink = detaildata.xpath('//div[@class="jxTradingPublic"]//iframe/@src').text().strip()
                    detaillink = re.findall('\?(.*)',detaillink)[0]
                    detaillink = 'http://lzggzyjy.lanzhou.gov.cn/TPBidder/zhmanagemis/pages/webgonggao/webgonggao_DetailAction.action?cmd=page_Load&{}'.format(detaillink)

                    date = item.xpath('''//i/text()''').text().strip()
                    date = str(date).replace("-", "")
                    publicTime = date
                    if self.getdumps(link):
                        continue
                    uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, link)) + str(uuid.uuid3(uuid.NAMESPACE_DNS, link))
                    ctime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    location = "甘肃省"
                    service = ''
                    industry = ""
                    post = {
                        "uuid": uid,  # md5
                        "detailUrl": detaillink,  # url
                        "name": title,  # 标题
                        "location": location,  # 地区
                        "publicTime": publicTime,  # 公布时间
                        "tag": "中标公告",  # 标签
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

#         titles = data.xpathall('//a[@class="btn btn-default article-list-single"]/@title')
#         links = data.xpathall('//a[@class="btn btn-default article-list-single"]/@href')
#         dates = data.xpathall('//span[@class="article-list-date"]/text()')

        if from_tag_url=='http://www.gansubidding.com/DataHandlers/PagerHandler.ashx?pageIndex=1&pageSize=50':
            tag = "招标公告"
        elif from_tag_url =='http://www.gansubidding.com/DataHandlers/CorrectList.ashx?pageIndex=1&pageSize=50':
            tag = "变更公告"
        else:
            tag ="中标公告"

        titles = re.findall('title="(.*?)"',unicode_html_body,re.S)
        dates = re.findall('class="mdate">(.*?)</span>',unicode_html_body,re.S)
        links = re.findall('href="(.*?)"',unicode_html_body,re.S)
        for title,date,link in zip(titles,dates,links):
            title = title.strip()
            date = str(date)
            dateList = date.split('/')
            if len(dateList[1]) == 1:
                dateList[1] = '{}{}'.format('0', dateList[1])
            if len(dateList[2]) == 1:
                dateList[2] = '{}{}'.format('0', dateList[2])
            date = '{}{}{}'.format(dateList[0], dateList[1], dateList[2])
            publicTime = date
            link = urljoin('http://www.gansubidding.com',str(link))


            if self.getdumps(link):
                continue
            link = str(link)
            uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, link)) + str(uuid.uuid3(uuid.NAMESPACE_DNS, link))
            ctime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            location = "甘肃省"
            service = ''
            industry = ""
            post = {
                "uuid": uid,  # md5
                "detailUrl": link,  # url
                "name": title,  # 标题
                "location": location,  # 地区
                "publicTime": publicTime,  # 公布时间
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
        if self.conn.sismember("dumps:ggzyjygansu", url):
            return True  # 在里面
        else:
            print "入redis：去重库"
            self.conn.sadd("dumps:ggzyjygansu", url)
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

    url = "http://www.gansubidding.com/DataHandlers/PagerHandler.ashx?pageIndex=1&pageSize=50"
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
