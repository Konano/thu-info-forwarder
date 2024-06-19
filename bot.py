import json
import logging
import sys
import time
from datetime import datetime
from typing import Any, cast

import schedule
from mastodon.errors import (MastodonInternalServerError, MastodonNetworkError,
                             MastodonNotFoundError)

from base import network, style
from base.config import CHANNEL, botToken, heartbeatURL
from base.data import localDict
from base.debug import eprint
from base.log import logger
from base.mastodon import mastodon
from base.telegram import deleteMessage, sendMessage
from crawler import checkURL, crawlNews

# Test mode
testmode = False


def setTestmode():
    global testmode
    testmode = True


def sendHeartbeat():
    try:
        network.get(heartbeatURL)
        if testmode:
            print("HEARTBEAT OK")
    except Exception as e:
        eprint(e)


assert mastodon is not None, 'no Mastodon instance'


all_news = localDict('news')
all_urls = set(url for url in all_news)
now_urls = set(url for url, data in all_news.items() if data['homepage'])

logger.info(f'Number of news: {len(all_urls)}')
logger.info(f'Number of news on the homepage: {len(now_urls)}')


def run():
    """
    Detect news and send to channels
    """
    insert_num = 0  # Number of news published
    delete_num = 0  # Number of news removed

    news = cast(list[dict[str, Any]], crawlNews())
    for x in news:
        if x['url'] not in all_urls:
            if not testmode:

                # Send to Pipeline channel
                sendMessage(botToken, CHANNEL['pipe'], json.dumps({'type': 'newinfo', 'data': x}))

                # Send to THU INFO channel
                try:
                    msgID_1 = sendMessage(botToken, CHANNEL['thu_info'],
                                          style.telegram(x), parse_mode='MarkdownV2')
                except Exception as e:
                    eprint(e)
                    msgID_1 = -1

                # Send to thu.closed.social
                try:
                    msgID_2 = mastodon.toot(style.mastodon(x)).id
                except (MastodonInternalServerError, MastodonNetworkError):
                    msgID_2 = -1
                except Exception as e:
                    eprint(e)
                    msgID_2 = -1
            else:
                msgID_1 = msgID_2 = -1

            x['homepage'] = True
            x['deleted'] = False
            x['createTime'] = datetime.now()
            x['msgID'] = {'thu_info': msgID_1, 'closed': msgID_2}
            all_news.set(x['url'], x)
            all_urls.add(x['url'])
            now_urls.add(x['url'])
            insert_num += 1

    # Check whether the news that has not appeared on the homepage is deleted
    for u in now_urls - set(x['url'] for x in news):
        all_news[u]['homepage'] = False

        if not checkURL(u):
            all_news[u]['deleted'] = True
            delete_num += 1
            if not testmode:

                # Delete from Pipeline channel
                sendMessage(botToken, CHANNEL['pipe'], json.dumps({'type': 'delinfo', 'data': u}))

                # Delete from THU INFO channel
                if all_news[u]['msgID']['thu_info'] > 0:
                    deleteMessage(botToken, CHANNEL['thu_info'], all_news[u]['msgID']['thu_info'])

                # Delete from thu.closed.social
                try:
                    if all_news[u]['msgID']['closed'] > 0:
                        mastodon.status_delete(all_news[u]['msgID']['closed'])
                except MastodonNotFoundError as e:
                    eprint(e, logging.DEBUG)
                except Exception as e:
                    eprint(e)

        all_news.dump()

    now_urls.clear()
    now_urls.update(x['url'] for x in news)

    if insert_num > 0 or delete_num > 0:
        logger.info(f'Homepage: {len(now_urls)}, New: {insert_num}, Del: {delete_num}')
        all_news.dump()

    sendHeartbeat()


def test():
    setTestmode()
    run()
    exit()


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == '--test':
        test()
    try:
        run()
        schedule.every().minute.do(run)
        while True:
            schedule.run_pending()
            time.sleep(10)
    except Exception as e:
        eprint(e, logging.ERROR)
    except KeyboardInterrupt:
        pass
