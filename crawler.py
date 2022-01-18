import requests
from bs4 import BeautifulSoup
import http.cookiejar as HC
import json
import html

session = requests.session()
session.cookies = HC.LWPCookieJar(filename='secret/cookies')
try:
    session.cookies.load(ignore_discard=True)
except:
    pass


def detectInfo(nextpage=False):
    error_count = 0
    page = 1 if not nextpage else 2
    while error_count <= 1:
        try:
            csrf = session.cookies._cookies['info2021.tsinghua.edu.cn']['/']['XSRF-TOKEN'].value
            url = f'https://info2021.tsinghua.edu.cn/b/info/xxfb_fg/xnzx/template/more?oType=mr&lmid=all&lydw=&currentPage={page}&length=30&_csrf={csrf}'
            res = session.post(url, timeout=(5, 10)).text
            res = json.loads(res)
            assert res['result'] == 'success'
        except Exception as e:
            error_count += 1
            session.get(
                'https://info2021.tsinghua.edu.cn/f/info/xxfb_fg/xnzx/template/more?lmid=all', timeout=(5, 10))
            session.cookies.save(ignore_discard=True)
            continue

        news = []
        for x in res['object']['dataList']:
            news.append({
                'title': html.unescape(x['bt']),
                'source': x['dwmc_show'],
                'date': x['time'].split(' ')[0].replace('-', '.'),
                'url': f'https://info2021.tsinghua.edu.cn' + x['url']})
        if len(news) == 0:
            raise Exception(url)
        return news

    raise Exception('error in detectInfo')


def detectInfoAcademic(nextpage=False):
    if nextpage:
        return []
    error_count = 0
    while error_count <= 1:
        try:
            csrf = session.cookies._cookies['info2021.tsinghua.edu.cn']['/']['XSRF-TOKEN'].value
            url = f'https://info2021.tsinghua.edu.cn/b/hdrc_fg/api/xxfb?_csrf={csrf}'
            res = session.post(url, timeout=(5, 10)).text
            res = json.loads(res)
            assert res['result'] == 'success'
        except Exception:
            error_count += 1
            session.get(
                'https://info2021.tsinghua.edu.cn/f/info/xxfb_fg/xnzx/template/more?lmid=all', timeout=(5, 10))
            session.cookies.save(ignore_discard=True)
            continue

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
                'url': f'https://info2021.tsinghua.edu.cn' + x['url']})
        if len(news) == 0:
            raise Exception(url)
        return news

    raise Exception('error in detectInfoAcademic')


def detectLibrary(url, nextpage=False):
    html = requests.get(url, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    if nextpage:
        __url = bs.select(
            'body > div.main > div > div > div > span.p_pages > span.p_next.p_fun > a')
        if len(__url) == 0:
            return []
        url = url[::-1].split('/', 1)[1][::-1] + '/' + __url[0].get('href')
        html = requests.get(url, timeout=(5, 10)).content
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
            'url': 'https://lib.tsinghua.edu.cn/'+each.get('href').replace('../', '')})
    if len(news) == 0:
        raise Exception(url)
    return news


def detectMyhome(nextpage=False):
    url = 'http://myhome.tsinghua.edu.cn/Netweb_List/News_notice.aspx'
    if nextpage:
        url += '?page=2'
    html = requests.get(url, timeout=(5, 10)).content
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
            'url': 'http://myhome.tsinghua.edu.cn/Netweb_List/'+each.get('href')})
    if len(news) == 0:
        raise Exception(url)
    return news


def detectNews(nextpage=False):
    url = 'https://www.tsinghua.edu.cn/news/zxdt.htm'
    html = requests.get(url, timeout=(5, 10)).content
    bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
    if nextpage:
        __url = bs.select(
            'body > div.rem12 > div.left > div.fanye.pcfyt > ul > div > span.p_pages > span.p_next.p_fun > a')[0]
        url = url[::-1].split('/', 1)[1][::-1] + '/' + __url.get('href')
        html = requests.get(url, timeout=(5, 10)).content
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
            'url': url.get('href').replace('../', 'http://www.tsinghua.edu.cn/')})
    if len(news) == 0:
        raise Exception(url)
    return news


def detectOffice(url, nextpage=False):
    if nextpage:
        url += '&pageno=2'
    html = requests.get(url, timeout=(5, 10)).content
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
                'url': 'http://xxbg.cic.tsinghua.edu.cn/oath/' + url})
    if len(news) == 0:
        raise Exception(url)
    return news
