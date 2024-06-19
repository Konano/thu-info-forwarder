import functools
import html
import json
import logging
import time
from typing import Literal, cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from base import network
from base.data import localDict
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
    network.session_get('https://info.tsinghua.edu.cn/f/info/xxfb_fg/xnzx/template/more?lmid=all')
    network.session.cookies.save(ignore_discard=True)  # type: ignore


def getCSRF() -> str:
    cookies = network.session.cookies
    csrf: str = cookies._cookies['info.tsinghua.edu.cn']['/']['XSRF-TOKEN'].value  # type: ignore
    return csrf


# info - 校内资讯 - 全部
@attempt(1, loginInfo)
def detectInfo(oType: Literal['xs', 'mr']) -> list[dict[str, str]]:
    # xs: students, mr: teachers
    page_url = f'https://info.tsinghua.edu.cn/b/info/xxfb_fg/xnzx/template/more?oType={oType}&lmid=all&lydw=&currentPage=1&length=30&_csrf={getCSRF()}'
    resp = network.session_post(page_url).json()
    try:
        assert resp['result'] == 'success'
        news: list[dict[str, str]] = []
        for x in resp['object']['dataList']:
            news.append({
                'title': html.unescape(x['bt']).strip(),
                'source': x['dwmc_show'],
                'date': x['time'].split(' ')[0],
                'url': urljoin("https://info.tsinghua.edu.cn/", x['url'])})
        if len(news) == 0:
            logger.warning(f"The number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, json.dumps(resp), 'json')
        raise e
    return news


# info - 活动日程 - 学术活动
@attempt(1, loginInfo)
def detectInfoAcademic() -> list[dict[str, str]]:
    page_url = f'https://info.tsinghua.edu.cn/b/hdrc_fg/index/all?_csrf={getCSRF()}'
    data = {'cjf': -1, 'hdlxm': 100}
    resp = network.session_post(page_url, data=data).json()
    try:
        assert resp['result'] == 'success'
        news: list[dict[str, str]] = []
        for lst in resp['object']['resultList']:
            for x in lst['hdrcList']:
                news.append({
                    'title': html.unescape(x['bt']).strip(),
                    'source': '学术活动',
                    'date': x['hdrq'],
                    'url': f'https://info.tsinghua.edu.cn/f/info/hdrc_fg/common/detail?hdrc_id=' + x['id']})
        if len(news) == 0:
            logger.warning(f"The number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, json.dumps(resp), 'json')
        raise e
    return news


def detectMyhome() -> list[dict[str, str]]:
    page_url = 'http://myhome.tsinghua.edu.cn/Netweb_List/News_notice.aspx'
    html = network.get(page_url).content
    try:
        bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
        content = bs.select(
            'table > tr > td:nth-child(2) > div > div.blueline.margin5 > div > table > tr > td:nth-child(2) > a')
        dates = bs.select(
            'table > tr > td:nth-child(2) > div > div.blueline.margin5 > div > table > tr > td:nth-child(3)')[1:]
        sources = bs.select(
            'table > tr > td:nth-child(2) > div > div.blueline.margin5 > div > table > tr > td:nth-child(4)')[1:]

        news: list[dict[str, str]] = []
        for each, date, source in zip(content, dates, sources):
            title = cast(str, each.get('title'))
            href = cast(str, each.get('href'))
            news.append({
                'title': title.strip(),
                'source': source.get_text().strip(),
                'date': date.get_text().strip()[:10],
                'url': urljoin(page_url, href)})
        if len(news) == 0:
            archive(page_url, html, 'html')
            logger.warning(f"The number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, html, 'html')
        raise e
    return news


def detectNews() -> list[dict[str, str]]:
    page_url = 'https://www.tsinghua.edu.cn/news/zxdt.htm'
    html = network.get(page_url).content
    try:
        bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
        dates = bs.select('body > div.rem12 > div.left > ul > li > a > div.sj')
        titles = bs.select('body > div.rem12 > div.left > ul > li > a > div.tit > p')
        urls = bs.select('body > div.rem12 > div.left > ul > li > a')

        news: list[dict[str, str]] = []
        for title, date, url in zip(titles, dates, urls):
            date = date.get_text().strip().split('\n')
            href = cast(str, url.get('href'))
            news.append({
                'title': title.get_text().strip(),
                'source': '清华新闻网',
                'date': date[1].replace('.', '-') + '-' + date[0],
                'url': urljoin(page_url, href)})
        if len(news) == 0:
            archive(page_url, html, 'html')
            logger.warning(f"The number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, html, 'html')
        raise e
    return news


def detectLibrary(page_url: str, allowzero=False) -> list[dict[str, str]]:
    html = network.get(page_url).content
    try:
        bs = BeautifulSoup(html, 'lxml', from_encoding='utf-8')
        content = bs.select('body > div.main > div > div > ul > li > div.notice-list-tt > a')
        bs_date = bs.select('body > div.main > div > div > ul > li > div.notice-date')
        source = bs.select('body > div.ban > h3')[0].get_text().strip()

        news: list[dict[str, str]] = []
        for each, date in zip(content, bs_date):
            href = cast(str, each.get('href'))
            news.append({
                'title': each.get_text(),
                'source': '图书馆'+source,
                'date': date.get_text().strip()[:10].replace('/', '-'),
                'url': urljoin(page_url, href)})
        if not allowzero and len(news) == 0:
            archive(page_url, html, 'html')
            logger.warning(f"The number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, html, 'html')
        raise e
    return news


def detectOffice(page_url: str) -> list[dict[str, str]]:
    html = network.get(page_url).content
    try:
        bs = BeautifulSoup(html, 'lxml', from_encoding='gbk')
        source = bs.select(
            'body > table:nth-child(2) > tr > td > table > tr > td:nth-child(2)')[0].get_text().strip()
        dates = bs.select(
            'body > table:nth-child(3) > tr:nth-child(2) > td > table > tr > td:nth-child(2) > table > tr:nth-child(1) > td > table:nth-child(2) > tr > td:nth-child(2) > font')
        content = bs.select(
            'body > table:nth-child(3) > tr:nth-child(2) > td > table > tr > td:nth-child(2) > table > tr:nth-child(1) > td > table:nth-child(2) > tr > td:nth-child(2) > a')
        titles = cast(list[str], [x.get('title') for x in content])
        urls = cast(list[str], [x.get('href') for x in content])

        news: list[dict[str, str]] = []
        for date, title, url in zip(dates, titles, urls):
            date = date.get_text().strip().replace('-', '.')[1:-1]
            if date != '':
                news.append({
                    'title': title,
                    'source': source,
                    'date': date.replace('.', '-'),
                    'url': urljoin(page_url, url)})
        # if len(news) == 0:
        #     archive(page_url, html, 'html')
        #     logger.warning(f"the number of news is 0 ({page_url})")
    except Exception as e:
        archive(page_url, html, 'html')
        raise e
    return news


redirect = localDict('redirect')


def crawlNews() -> list[dict[str, str]]:
    while True:
        try:
            news: list[dict[str, str]] = []
            news += detectInfo('xs')
            news += detectInfo('mr')
            news += detectInfoAcademic()
            news += detectMyhome()
            news += detectNews()
            news += detectLibrary('https://lib.tsinghua.edu.cn/zydt.htm')
            news += detectLibrary('https://lib.tsinghua.edu.cn/tzgg/kgtz.htm')
            news += detectLibrary('https://lib.tsinghua.edu.cn/tzgg/sgwx.htm')
            news += detectLibrary('https://lib.tsinghua.edu.cn/tzgg/fwtz.htm')
            news += detectLibrary('https://lib.tsinghua.edu.cn/tzgg/wgtb.htm', True)
            news += detectLibrary('https://lib.tsinghua.edu.cn/tzgg/qtkx.htm')
            news += detectLibrary('https://lib.tsinghua.edu.cn/tzgg/gjtz.htm')
            news += detectOffice('https://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=2710')
            news += detectOffice('https://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=22')
            news += detectOffice('https://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=3303')

            # Check redirect
            for x in news:
                if x['url'] not in redirect:
                    orig_url = x['url']
                    real_url = network.get(orig_url).url
                    logger.debug(f'redirect: {orig_url} -> {real_url}')
                    redirect.set(orig_url, real_url)
                x['url'] = redirect.get(x['url'])
            break

        except Exception as e:
            eprint(e)
            logger.warning('Crawl failed, will retry in 60 seconds...')
            time.sleep(60)

    return news


def checkURL(url: str) -> bool:
    return network.get(url, validate_status=False).status_code == 200
