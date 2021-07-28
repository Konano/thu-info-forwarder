import re
import requests
from bs4 import BeautifulSoup


def detect(url):
    html = requests.get(url, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('.cont_list > li')
    news = []
    for each in content:
        tmp = re.split('\xa0\xa0|\t\n', each.get_text().strip())
        news.append({'title'  : tmp[0],
                     'source' : tmp[1][1:-1],
                     'date'   : tmp[2],
                     'url'    : each.find('a').get('href').strip()})
    if len(news) == 0:
        raise Exception(url)
    return news


def detectBoard():
    url = 'http://postinfo.tsinghua.edu.cn/f/zhongyaogonggao/more'
    html = requests.get(url, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('table > tr > td > a')
    news = []
    for each in content:
        news.append({'title'  : each.get('title'),
                     'source' : '重要公告',
                     'url'    : each.get('href').strip()})
    if len(news) == 0:
        raise Exception(url)
    return news


def detectLibrary():
    url = 'http://lib.tsinghua.edu.cn/tzgg.htm'
    html = requests.get(url, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('body > div.main > div > div > ul > li > div.notice-list-tt > a')
    bs_date = bs.select('body > div.main > div > div > ul > li > div.notice-date')
    source = bs.select('body > div.ban > h3')[0].get_text().strip()
    news = []
    for each, date in zip(content, bs_date):
        news.append({'title'  : each.get_text(),
                     'source' : '图书馆' + source,
                     'date'   : date.get_text().strip()[:10].replace('/', '.'),
                     'url'    : 'http://lib.tsinghua.edu.cn/'+each.get('href')})
    if len(news) == 0:
        raise Exception(url)

    url = 'http://lib.tsinghua.edu.cn/zydt.htm'
    html = requests.get(url, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('body > div.main > div > div > ul > li > div.notice-list-tt > a')
    bs_date = bs.select('body > div.main > div > div > ul > li > div.notice-date')
    source = bs.select('body > div.ban > h3')[0].get_text().strip()
    __news = []
    for each, date in zip(content, bs_date):
        __news.append({'title'  : each.get_text(),
                       'source' : '图书馆' + source,
                       'date'   : date.get_text().strip()[:10].replace('/', '.'),
                       'url'    : 'http://lib.tsinghua.edu.cn/'+each.get('href')})
    if len(__news) == 0:
        raise Exception(url)

    return news + __news


def detectMyhome():
    url = 'http://myhome.tsinghua.edu.cn/Netweb_List/News_notice.html'
    html = requests.get(url, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('table > tr > td:nth-child(2) > div > div.blueline.margin5 > div > table > tr > td:nth-child(2) > a')[1:]
    bs_date = bs.select('table > tr > td:nth-child(2) > div > div.blueline.margin5 > div > table > tr > td:nth-child(3)')[1:]
    news = []
    for each, date in zip(content, bs_date):
        news.append({'title'  : each.get_text().strip(),
                     'source' : '家园网公告',
                     'date'   : date.get_text().strip()[:10].replace('-', '.'), # todo
                     'url'    : 'http://myhome.tsinghua.edu.cn/Netweb_List/'+each.get('href')})
    if len(news) == 0:
        raise Exception(url)
    return news
