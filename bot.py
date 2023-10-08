import json
import logging
import sys
import time
from datetime import datetime

import schedule
from mastodon.errors import (MastodonInternalServerError, MastodonNetworkError,
                             MastodonNotFoundError)

import crawler
from base import format, network
from base.config import CHANNEL, MASTODON, botToken, heartbeatURL
from base.data import localDict
from base.debug import eprint
from base.log import logger
from base.mastodon import mastodon_init, mastodon_login
from base.telegram import deleteMessage, sendMessage

mastodon = None
while mastodon is None:
    try:
        mastodon = mastodon_login(**MASTODON)
        if mastodon is None:
            mastodon_init(**MASTODON)
            time.sleep(60)
    except MastodonNetworkError as e:
        time.sleep(60)
    except Exception as e:
        eprint(e)
        time.sleep(60)


def sendHeartbeat():
    try:
        network.get(heartbeatURL)
    except Exception as e:
        eprint(e)


redirect = localDict('redirect')


def get_news(secondpage=False):
    while True:
        try:
            news = []
            news += crawler.detectInfo(secondpage)
            news += crawler.detectInfoAcademic(secondpage)
            news += crawler.detectMyhome(secondpage)
            news += crawler.detectNews(secondpage)
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/zydt.htm', secondpage)
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/kgtz.htm', secondpage)
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/sgwx.htm', secondpage)
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/fwtz.htm', secondpage)
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/wgtb.htm', secondpage, True)
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/qtkx.htm', secondpage)
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/gjtz.htm', secondpage)
            news += crawler.detectOffice(
                'http://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=2710', secondpage)
            news += crawler.detectOffice(
                'http://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=22', secondpage)
            news += crawler.detectOffice(
                'http://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=3303', secondpage)
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
            time.sleep(60)
            continue
    return news


news = localDict('news')

all_urls = set(url for url in news)
front_urls = set(url for url, data in news.items() if data['firstpage'])

logger.info(f'all: {len(all_urls)}, front: {len(front_urls)}')


def detect():
    insert_count = 0
    delete_count = 0

    firstpage_news = get_news()
    for x in firstpage_news:
        if x['url'] not in all_urls:

            # Send to Pipeline channel
            sendMessage(botToken, CHANNEL['pipe'], json.dumps(
                {'type': 'newinfo', 'data': x}))

            # Send to THU INFO channel
            msgID = sendMessage(
                botToken, CHANNEL['thu_info'], format.telegram(x), parse_mode='MarkdownV2')

            # Send to thu.closed.social
            try:
                __msgID = mastodon.toot(format.mastodon(x)).id
            except (MastodonInternalServerError, MastodonNetworkError):
                __msgID = -1
            except Exception as e:
                eprint(e)
                __msgID = -1

            x['firstpage'] = True
            x['deleted'] = False
            x['createTime'] = datetime.now()
            x['msgID'] = {'thu_info': msgID, 'closed': __msgID}
            news.set(x['url'], x)
            all_urls.add(x['url'])
            insert_count += 1

    firstpage_urls = set(x['url'] for x in firstpage_news)
    secondpage_urls = None

    for u in front_urls - firstpage_urls:
        news[u]['firstpage'] = False
        if secondpage_urls is None:
            secondpage_urls = set(x['url'] for x in get_news(secondpage=True))
        if u in secondpage_urls:
            news[u]['deleted'] = False
        else:
            news[u]['deleted'] = True
            delete_count += 1

            # Delete from Pipeline channel
            sendMessage(botToken, CHANNEL['pipe'], json.dumps(
                {'type': 'delinfo', 'data': u}))

            # Delete from THU INFO channel
            msgID = news[u]['msgID']['thu_info']
            if msgID > 0:
                deleteMessage(botToken, CHANNEL['thu_info'], msgID)

            # Delete from thu.closed.social
            try:
                __msgID = news[u]['msgID']['closed']
                if __msgID > 0:
                    mastodon.status_delete(__msgID)
            except MastodonNotFoundError as e:
                eprint(e, logging.DEBUG)
            except Exception as e:
                eprint(e)
        news.dump()

    front_urls.clear()
    front_urls.update(firstpage_urls)

    if insert_count > 0 or delete_count > 0:
        logger.info(
            f'firstpage: {len(firstpage_urls)}, new: {insert_count}, del: {delete_count}')
        news.dump()

    sendHeartbeat()


def test():
    detect()
    exit()


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == '--test':
        test()
    try:
        detect()
        schedule.every().minute.do(detect)
        while True:
            schedule.run_pending()
            time.sleep(10)
    except Exception as e:
        eprint(e, logging.ERROR)
    except KeyboardInterrupt:
        pass
