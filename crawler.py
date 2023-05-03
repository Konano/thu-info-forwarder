import functools
import html
import json
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from base import network
from base.debug import archive, eprint
from base.log import logger


def attempt(times: int, fix_func):
    def decorate(func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    eprint(e, logging.DEBUG)
                    fix_func()
            return func(*args, **kwargs)
        return wrap
    return decorate


def loginInfo():
    network.session_get(
        'https://info2021.tsinghua.edu.cn/f/info/xxfb_fg/xnzx/template/more?lmid=all')
    network.session.cookies.save(ignore_discard=True)


@attempt(1, loginInfo)
def detectInfo(nextpage=False):
    page = 1 if not nextpage else 2
    csrf = network.session.cookies._cookies['info2021.tsinghua.edu.cn']['/']['XSRF-TOKEN'].value
    page_url = f'https://info2021.tsinghua.edu.cn/b/info/xxfb_fg/xnzx/template/more?oType=mr&lmid=all&lydw=&currentPage={page}&length=30&_csrf={csrf}'
    text = network.session_post(page_url).text
    try:
        res = json.loads(text)
        assert res['result'] == 'success'
        news = []
        for x in res['object']['dataList']:
            news.append({
                'title': html.unescape(x['bt']),
                'source': x['dwmc_show'],
                'date': x['time'].split(' ')[0].replace('-', '.'),
                'url': urljoin(page_url, x['url'])})
        if len(news) == 0:
            archive(page_url, html, 'html')
            logger.warning(f"the number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, text, 'json')
        raise e
    return news


@attempt(1, loginInfo)
def detectInfoAcademic(nextpage=False):
    if nextpage:
        return []
    csrf = network.session.cookies._cookies['info2021.tsinghua.edu.cn']['/']['XSRF-TOKEN'].value
    page_url = f'https://info2021.tsinghua.edu.cn/b/hdrc_fg/api/xxfb?_csrf={csrf}'
    text = network.session_post(page_url).text
    try:
        res = json.loads(text)
        assert res['result'] == 'success'
        news = []
        for x in res['object']['lm_1']['hdrcList']:
            news.append({
                'title': html.unescape(x['bt']),
                'source': res['object']['lm_1']['hdlxmc'],
                'date': x['hdrq'].replace('-', '.'),
                'url': f'https://info2021.tsinghua.edu.cn' + x['url']})
        for x in res['object']['lm_2']['hdrcList']:
            news.append({
                'title': html.unescape(x['bt']),
                'source': res['object']['lm_2']['hdlxmc'],
                'date': x['hdrq'].replace('-', '.'),
                'url': urljoin(page_url, x['url'])})
        if len(news) == 0:
            archive(page_url, html, 'html')
            logger.warning(f"the number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, text, 'json')
        raise e
    return news


def detectLibrary(page_url, nextpage=False):
    html = network.get(page_url).content
    try:
        bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
        if nextpage:
            url = bs.select(
                'body > div.main > div > div > div > span.p_pages > span.p_next.p_fun > a')
            if len(url) == 0:
                return []
            page_url = urljoin(page_url, url[0].get('href'))
            html = network.get(page_url).content
            bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
        content = bs.select(
            'body > div.main > div > div > ul > li > div.notice-list-tt > a')
        bs_date = bs.select(
            'body > div.main > div > div > ul > li > div.notice-date')
        source = bs.select('body > div.ban > h3')[0].get_text().strip()
        news = []
        for each, date in zip(content, bs_date):
            news.append({
                'title': each.get_text(),
                'source': '图书馆'+source,
                'date': date.get_text().strip()[:10].replace('/', '.'),
                'url': urljoin(page_url, each.get('href'))})
        if len(news) == 0:
            archive(page_url, html, 'html')
            logger.warning(f"the number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, html, 'html')
        raise e
    return news


def detectMyhome(nextpage=False):
    page_url = 'http://myhome.tsinghua.edu.cn/Netweb_List/News_notice.aspx' + \
        ('?page=2' if nextpage else '')
    html = network.get(page_url).content
    try:
        bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
        content = bs.select(
            'table > tr > td:nth-child(2) > div > div.blueline.margin5 > div > table > tr > td:nth-child(2) > a')
        dates = bs.select(
            'table > tr > td:nth-child(2) > div > div.blueline.margin5 > div > table > tr > td:nth-child(3)')[1:]
        sources = bs.select(
            'table > tr > td:nth-child(2) > div > div.blueline.margin5 > div > table > tr > td:nth-child(4)')[1:]
        news = []
        for each, date, source in zip(content, dates, sources):
            news.append({
                'title': each.get('title').strip(),
                'source': source.get_text().strip(),
                'date': date.get_text().strip()[:10].replace('-', '.'),
                'url': urljoin(page_url, each.get('href'))})
        if len(news) == 0:
            archive(page_url, html, 'html')
            logger.warning(f"the number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, html, 'html')
        raise e
    return news


def detectNews(nextpage=False):
    page_url = 'https://www.tsinghua.edu.cn/news/zxdt.htm'
    html = network.get(page_url).content
    try:
        bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
        if nextpage:
            url = bs.select(
                'body > div.rem12 > div.left > div.fanye.pcfyt > ul > div > span.p_pages > span.p_next.p_fun > a')[0]
            page_url = urljoin(page_url, url.get('href'))
            html = network.get(page_url).content
            bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
        titles = bs.select(
            'body > div.rem12 > div.left > ul > li > a > div.tit > p')
        dates = bs.select('body > div.rem12 > div.left > ul > li > a > div.sj')
        urls = bs.select('body > div.rem12 > div.left > ul > li > a')
        news = []
        for title, date, url in zip(titles, dates, urls):
            _date = date.get_text().strip().split('\n')
            news.append({
                'title': title.get_text().strip(),
                'source': '清华新闻网',
                'date': _date[1] + '.' + _date[0],
                'url': urljoin(page_url, url.get('href'))})
        if len(news) == 0:
            archive(page_url, html, 'html')
            logger.warning(f"the number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, html, 'html')
        raise e
    return news


def detectOffice(page_url, nextpage=False):
    if nextpage:
        page_url += '&pageno=2'
    html = network.get(page_url).content
    try:
        bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
        source = bs.select(
            'body > table:nth-child(2) > tr > td > table > tr > td:nth-child(2)')[0].get_text().strip()
        content = bs.select(
            'body > table:nth-child(3) > tr:nth-child(2) > td > table > tr > td:nth-child(2) > table > tr:nth-child(1) > td > table:nth-child(2) > tr > td:nth-child(2) > a')
        titles = [x.get('title') for x in content]
        urls = [x.get('href') for x in content]
        dates = bs.select(
            'body > table:nth-child(3) > tr:nth-child(2) > td > table > tr > td:nth-child(2) > table > tr:nth-child(1) > td > table:nth-child(2) > tr > td:nth-child(2) > font')
        news = []
        for title, date, url in zip(titles, dates, urls):
            date = date.get_text().strip().replace('-', '.')[1:-1]
            if date != '':
                news.append({
                    'title': title,
                    'source': source,
                    'date': date,
                    'url': urljoin(page_url, url)})
        if len(news) == 0:
            archive(page_url, html, 'html')
            logger.warning(f"the number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, html, 'html')
        raise e
    return news
