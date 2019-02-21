##coding=utf-8

#############################################################################
# Copyright (c) 2018  - Beijing Intelligent Star, Inc.  All rights reserved


# 	绍兴市柯桥区广播电视总台


# 2018-12-12：徐鹏


import datetime
import htmlparser
import re
import copy
import requests
from urlparse import urljoin
import spiderDefault
import myreadability
import json


class MySpider(spiderDefault.Spider):

    def __init__(self, cmd_args=None):
        spiderDefault.Spider.__init__(self, cmd_args=cmd_args)

        # 类别码，01新闻、02论坛、03博客、04微博 05平媒 06微信  07 视频、99搜索引擎
        self.info_flag = "01"
        # 网站名称
        self.siteName = '绍兴市柯桥区广播电视总台'
        # 网站一级域名
        self.site_domain = 'scbtv.cn'

        self.start_urls = [
            # 列表页链接
            'http://www.scbtv.cn/index.php?s=/home/index/news/c_id/2.html',#广电动态
            'http://www.scbtv.cn/index.php?s=/home/index/news/c_id/46.html',#柯桥新闻
            'http://www.scbtv.cn/index.php?s=/home/index/news/c_id/47.html',#国内新闻
            'http://www.scbtv.cn/index.php?s=/home/index/news/c_id/48.html',#今日看点
            'http://www.scbtv.cn/index.php?s=/home/index/news/c_id/49.html',#廉政之窗
        ]
        # 网页编码
        # 例：self.encoding = 'gbk'
        self.encoding = 'utf-8'
        self.c_time = datetime.datetime.utcnow() - datetime.timedelta(days=3)
        self.page_url = {}
        self.max_interval = datetime.timedelta(days=3)
        # self.dedup_uri=None
        self.channel = ''

    def clear_special_xp(self, data, xp):
        # '''删除指定xpath数据'''
        data = copy.copy(data)
        result = data._root.xpath(xp)
        for i in result:
            try:
                i.getparent().remove(i)
            except Exception as e:
                log.logger.error(e)
        return data

    def get_detail_page_urls(self, data):
        '''
        从列表页获取详情页url; 返回列表
        '''
        detail_page_urls = []

        if data is not None:
            url = data.response.request.url
            # 包含详情页链接和时间的模块，一般以//tr、//li、//div等结尾
            # 例：loops = data.xpathall('''//div[contains(@class,"news-list2")]//li''')
            loops = data.xpathall('''//ul[@class="document-ul"]//div[2]''')

            for item in loops:  # 这时的item可以看做将解析到的模块当做新的网页打开，页面内只有解析到的模块，以解析的模块为顶级节点进行解析，而不再是标签

                # 此处不要再出现解析模块的Xpath，继续向子节点解析即可
                # 模块内解析详情页链接，一般以//@href结尾
                # 例：post_url = item.xpath('''//h3//a//@href''').text().strip()
                post_url = item.xpath('''//a//@href''').text().strip()
                if not post_url:
                    continue
                post_url = urljoin("http://www.scbtv.cn", post_url)
                # 模块内解析详情页时间，一般以//span、//div、//p等结尾，如没有则删除这三行
                # 例：ctime = item.xpath('''//div[@class="tail"]//span[1]''').datetime()
                # ctime = item.xpath('''//td[@align="center"]''').datetime()
                # if ctime < self.c_time:
                #     continue
                self.page_url[post_url] = url
                print post_url
                detail_page_urls.append(post_url)
            detail_page_urls = set(detail_page_urls)
        return detail_page_urls

    def get_detail_page_info(self, data):
        '''

        解析详情页信息；参数data可直接调用xpath,re等方法；
        返回值为字典类型
        '''

        url = data.response.request.url
        result = []
        pic_urls = []

        # 详情页内解析标题，一般以//text()结尾
        # title = data.xpath('''//div[@class="layout"]//h2//text()''').text().strip()
        title = data.xpath('''//div[@class="news-title"]//text()''').text().strip()

        gtime = datetime.datetime.utcnow()
        # 详情页内解析包含发布时间的模块，一般以//span、//div、//p结尾
        # ctime = data.xpath('''//div[@class="layout"]//div[@class="left"]''')

        ctime = data.xpath('''//div[@class="news-info"]/div[1]//text()''').regex('\d+-\d+-\d+').datetime()
        # ctime = gtime
        if ctime < self.c_time:
            return None
        # 详情页解析当前页面所属频道的面包屑，一般以//text()结尾
        # source = data.xpath('''//div[@class="add"]//a[last()]//text()''')
        channel = data.xpath('''//div[@class="top-location-div"]/a[2]//text()''').text().strip()

        # 详情页解析作者，一般以//text()结尾
        # source = data.xpath('''//div[@id="xl-headline"]//div[@class="left"]//text()''')
        source = self.siteName

        # 详情页解析来源，一般以//text()结尾，如没有，此字段=''
        # retweeted_source = data.xpath('''//div[@id="xl-headline"]//div[@class="left"]//text()''')
        retweeted_source = self.siteName

        # 详情页解析来源链接，一般以//@href结尾，如没有，此字段=''
        # 例：retweeted_status_url = data.xpath('''''')
        retweeted_status_url = ''

        list_page_url = self.page_url.get(url, '')

        content = ''
        content_xml = ''
        # 详情页解析正文，一般以//p、//div、//span等结尾
        # 例：content1 = data.xpathall('''//div[@class="news-con"]''')
        content1 = data.xpathall('''//div[@class="news-content"]''')
        for item in content1:
            # 此处填写需要排除的（不进行解析）元素，如有多个以‘|’分隔开，如没有，请将‘|？’删除，注意：‘//script’不要删除！
            # 例：content_str = self.clear_special_xp(item,'''//script''')
            content_str = self.clear_special_xp(item,
                                                '''//script|//style|//ignore_js_op/div|//span[@style="display:none"]|//font[@class="jammer"]''')
            content += content_str.text().strip()
            content_xml += content_str.data.encode('utf-8')

        content = title if not content else content
        # 此处解析真跟捏的图片，内容与上方content1后面填写的内容一致，后面的‘//img//@src’不要删除
        # 例：pic_urls_list = data.xpathall('''//div[@class="news-con"]//img//@src''')
        pic_urls_list = data.xpathall('''//div[@class="news-content"]//img/@src''')
        if pic_urls_list:
            for i in pic_urls_list:
                i = i.text().strip()
                # i = urljoin(url,i)
                pic_urls.append(i)

        post = {
            'title': title,
            'gtime': gtime,
            'ctime': ctime,
            'source': source,
            'retweeted_source': retweeted_source,
            'channel': channel,
            'list_page_url': list_page_url,
            'siteName': self.siteName + '-' + channel,
            'url': url,
            'content': content,
            'content_xml': content_xml,
        }
        if pic_urls:
            post.update({"pic_urls": pic_urls})
        if channel == self.siteName:
            post.update({"siteName": self.siteName})
        if retweeted_status_url:
            post.update({'retweeted_status_url': retweeted_status_url})
        result.append(post)
        return result


if __name__ == "__main__":
    spider = MySpider()
    spider.proxy_enable = False
    spider.init_dedup()
    spider.init_downloader()

    # 此处选填单测功能的详情页完整链接，仅用于测试上方的get_detail_page_info()函数
    # 例：url = 'http://news.dzwww.com/guoneixinwen/201806/t20180629_17546125.htm'
    url = '？'
    resp = spider.download(url)
    # resp.encoding="utf-8"
    res = spider.parse_detail_page(resp, url)

    if res is not None:
        for item in res:
            for k, v in item.iteritems():
                print k, v