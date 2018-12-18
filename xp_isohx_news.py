# coding=utf-8

#############################################################################
# Copyright (c) 2014  - Beijing Intelligent Star, Inc.  All rights reserved


'''''
文件名：
功能： 爬虫抓取配置文件

频道：中国认证信息网
代码历史：
徐鹏，创建代码
'''
import spider
import setting
import htmlparser
import re
import datetime
import sys
import copy

reload(sys)
from urlparse import urljoin


class MySpider(spider.Spider):
    def __init__(self, cmd_args=None):
        spider.Spider.__init__(self, cmd_args=cmd_args)

        self.siteName = "中国认证信息网"
        self.site_domain = 'http://www.isohx.net'
        # 类别码，01新闻、02论坛、03博客、04微博 05平媒 06微信  07 视频、99搜索引擎
        self.info_flag = "01"
        self.start_urls = [
            'http://www.isohx.net/news1.html'
        ]

        self.encoding = 'gb2312'
        # self.max_interval = None
        # self.dedup_uri=None
        self.ctim = {}
        self.max_interval = datetime.timedelta(days=3)
        self.c_time = datetime.datetime.utcnow() - datetime.timedelta(days=3)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36",
            }
        self.request_headers = {"headers": headers}

    def get_start_urls(self, data=None):
        return self.start_urls

    def parse(self, response):

        url_list = []
        if response is not None:
            try:
                response.encoding = self.encoding
                unicode_html_body = response.text
                data = htmlparser.Parser(unicode_html_body)
            except Exception, e:
                print "parse(): %s" % e
                return (url_list, None, None)

            urls = data.xpathall('''//div[@align="left"]/a''')

            purl = response.request.url
            if urls:
                for urla in urls:
                    url = urla.xpath("//@href").text()
                    # p_url = re.findall(r"-(\d+)",url)
                    # if p_url == []:
                    #     continue
                    # url = "http://bbs.pc186.com/forum.php?mod=forumdisplay&fid=%s&filter=author&orderby=dateline"%(p_url[0])
                    URL = 'http://www.isohx.net/'+url
                    url_list.append(URL)
        # return (url_list,  self.parse_next, None)
        return (url_list, None, None)

    # def parse_next(self, response):
    #
    #     url_list = []
    #     if response is not None:
    #         try:
    #             response.encoding = self.encoding
    #             unicode_html_body = response.text
    #             data = htmlparser.Parser(unicode_html_body)
    #         except Exception, e:
    #             print "parse(): %s"%e
    #             return (url_list, None, None)
    #         urls = data.xpathall('''//tbody[contains(@id,"normalthread")]''')
    #
    #         purl =response.request.url
    #         if urls:
    #             for urla in urls:
    #                 ctime = urla.xpath('''//td[@class="by"][1]/em/span|//td[@class="by"][1]/em/span/span/@title''').regex('\d+-\d+-\d+').datetime()
    #                 if ctime<self.c_time:
    #                     continue
    #                 url = urla.xpath("//th/a[last()]/@href").text()
    #                 t_url = re.findall(r"tid=(\d+)",url)
    #                 url = "http://bbs.pc186.com/thread-%s-1-1.html"%(t_url[0])
    #                 self.ctim[url] = ctime
    #                 #URL = 'http://www.0515bh.com'+url
    #                 url_list.append(url)
    #
    #
    #     return (url_list,  None, None)

    def clear_special_xp(self, data, xp):
        data = copy.copy(data)
        result = data._root.xpath(xp)
        for i in result:
            try:
                i.getparent().remove(i)
            except Exception as e:
                log.logger.error(e)
        return data

    def parse_detail_page(self, response=None, url=None):
        '''''
        解析内容页文本
        '''
        try:
            response.encoding = self.encoding
            unicode_html_body = response.text
            data = htmlparser.Parser(unicode_html_body)
        except Exception, e:
            print "parse_detail_page(): %s" % e
            return None
        if url is None:
            url = response.request.url

        result = []
        pic_urls = []
        delete_xpath = '''//script|//style|//ignore_js_op/div|//span[@style="display:none"]|//font[@class="jammer"]'''
        data = self.clear_special_xp(data, delete_xpath)
        gtime = datetime.datetime.utcnow()
        channel = data.xpath('''//td[@class="Color_01"]''').text()
        title = data.xpath('''//h2''').text().strip()
        # source = data.xpath('''//div[@class="wzy_nr_sm"]/div/span[1]''').text().strip()
        source = ""
        # visit_count = data.xpath('''//div[@class="wzy_nr_sm"]/div/span[3]//text()''').regex('\d+').int()
        visit_count = 0
        reply_count = 0
        # reply_count = data.xpath('''//a[@id="comment"]/text()''').regex("(\d+)").int()
        ctime = data.xpath('''//div[@class="content"]//div[@align="center"]/text()''').regex('\d+-\d+-\d+ \d+:\d+:\d+').datetime()
        if ctime < self.c_time:
            return
        content = data.xpath('''//div[@class="content"]//p''').text().strip()
        # imgs = data.xpathall('''//div[@id="MyContent"]//img/@src''')
        imgs = []
        if len(imgs) > 0:
            for i in imgs:
                img_url = i.text()
                img_url = urljoin(url, img_url)
                pic_urls.append(img_url)
        if not content:
            content = title

        post = {'title': title,
                'ctime': ctime,
                'gtime': gtime,
                'source': source,
                'channel': channel,
                'siteName': self.siteName + '-' + channel,
                'visitCount': [{'count': visit_count, 'spider_time': gtime}],
                'replyCount': [{'count': reply_count, 'spider_time': gtime}],
                'data_db': self.data_db,
                'url': url,
                'content': content,
                }
        # print post
        if pic_urls:
            post.update({'pic_urls': pic_urls})
        result.append(post)

        return result


if __name__ == '__main__':
    spider = MySpider()
    spider.proxy_enable = False
    spider.init_dedup()
    spider.init_downloader()

    # ------------ get_start_urls() ----------
    #    urls = spider.get_start_urls()
    #    for url in urls:
    #        print url

    # ------------ parse() ----------
    #    url = 'http://bbs.yantian.com.cn/forum.php?mod=forumdisplay&fid=1690'
    #    resp = spider.download(url)
    #    urls = spider.parse(resp)
    #    for url in urls:
    #        print url

    # ------------ parse_detail_page() ----------

    # url = 'http://www.kpren.com/thread-75948-1-1.html'
    url = 'http://www.isohx.net/news_detail/32.html'
    resp = spider.download(url)
    res = spider.parse_detail_page(resp, url)
    for item in res:
        for k, v in item.iteritems():
            print k, v
