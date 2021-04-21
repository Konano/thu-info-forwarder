import requests
from bs4 import BeautifulSoup
import re


def detect(URL):
    html = requests.get(URL, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('.cont_list > li')
    messages = []
    for each in content:
        tmp = re.split('\xa0\xa0|\t\n', each.get_text().strip())
        messages.append({'title' : tmp[0],
                         'source': tmp[1][1:-1],
                         'date'  : tmp[2],
                         'url'   : each.find('a').get('href').strip()})
    if len(messages) == 0:
        raise Exception(URL)
    return messages


def detectBoard(URL):
    html = requests.get(URL, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('table > tr > td > a')
    messages = []
    for each in content:
        messages.append({'title' : each.get('title'),
                         'source': '重要公告',
                         'url'   : each.get('href').strip()})
    if len(messages) == 0:
        raise Exception(URL)
    return messages


def detectLibrary(URL):
    html = requests.get(URL, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('body > div.main > div > div > ul > li > div.notice-list-tt > a')
    source = bs.select('body > div.ban > h3')[0].get_text().strip()
    messages = []
    for each in content:
        messages.append({'title' : each.get_text(),
                         'source': '图书馆' + source,
                         'url'   : 'http://lib.tsinghua.edu.cn/'+each.get('href')})
    if len(messages) == 0:
        raise Exception(URL)
    return messages


def detectMyhome(URL):
    html = requests.get(URL, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('table > tr > td:nth-child(2) > div > div.blueline.margin5 > div > table > tr > td:nth-child(2) > a')[1:]
    messages = []
    for each in content:
        messages.append({'title' : each.get_text().strip(),
                         'source': '家园网公告',
                         'url'   : 'http://myhome.tsinghua.edu.cn/Netweb_List/'+each.get('href')})
    if len(messages) == 0:
        raise Exception(URL)
    return messages


def request(URL):
    return requests.get(URL).content.decode('utf-8')
