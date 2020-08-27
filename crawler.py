import requests
from bs4 import BeautifulSoup
import re


def detect(URL):
    html = requests.get(URL).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('.cont_list > li')
    messages = []
    for each in content:
        tmp = re.split('\xa0\xa0|\t\n', each.get_text().strip())
        messages.append({'title' : tmp[0],
                         'source': tmp[1][1:-1],
                         'date'  : tmp[2],
                         'url'   : each.find('a').get('href').strip()})
    assert len(messages) > 0
    return messages


def detectBoard(URL):
    html = requests.get(URL).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('table > tr > td > a')
    messages = []
    for each in content:
        messages.append({'title' : each.get('title'),
                         'source': '重要公告',
                         'url'   : each.get('href').strip()})
    assert len(messages) > 0
    return messages


def detectLibrary(URL):
    html = requests.get(URL).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    content = bs.select('table > tbody > tr > td > a')
    messages = []
    for each in content:
        messages.append({'title' : each.get_text(),
                         'source': '图书馆公告',
                         'url'   : 'http://lib.tsinghua.edu.cn'+each.get('href')})
    assert len(messages) > 0
    return messages


def request(URL):
    return requests.get(URL).content.decode('utf-8')
