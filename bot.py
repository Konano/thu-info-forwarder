import crawler
import format
from log import logger

import time
import json
import pymongo
import pymongo.errors
import requests
import traceback
import configparser
from datetime import datetime
from mastodon import Mastodon


config = configparser.ConfigParser()
config.read('config.ini')

db = pymongo.MongoClient(
    f'mongodb://{config["MONGODB"]["user"]}:{config["MONGODB"]["pwd"]}@{config["MONGODB"]["host"]}:{config["MONGODB"]["port"]}/')['service']['info']

# Mastodon.create_app(
#     'bot',
#     api_base_url = config['MASTODON']['url'],
#     to_file = config['MASTODON']['clientcred']
# )
mastodon = Mastodon(
    client_id=config['MASTODON']['clientcred'],
    api_base_url=config['MASTODON']['url']
)
mastodon.log_in(
    username=config['MASTODON']['email'],
    password=config['MASTODON']['pwd'],
    to_file=config['MASTODON']['usercred']
)
mastodon = Mastodon(
    access_token=config['MASTODON']['usercred'],
    api_base_url=config['MASTODON']['url']
)


def sendHeartbeat():
    try:
        requests.get(url=config['HEARTBEAT']['url'], timeout=(5, 10))
    except Exception as e:
        logger.debug(traceback.format_exc())
        logger.warning(e)


UA = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'


# Send msg to Telegram
def sendMessage(token, chat_id, text, parse_mode=None):
    error_count = 0
    while error_count < 6:
        headers = {'User-Agent': UA}
        url = f'https://tg.nano.ac/bot{token}/sendMessage'
        params = {'text': text, 'chat_id': chat_id,
                  'disable_web_page_preview': True}
        if parse_mode != None:
            params['parse_mode'] = parse_mode
        try:
            response = requests.get(
                url=url, params=params, headers=headers, timeout=(5, 10))
            assert response.status_code == 200
            logger.debug(response.json())
            return response.json()['result']['message_id']
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.warning(e)
            error_count += 1
        time.sleep(5)
    raise Exception('Send msg TIMEOUT')


# Delete msg from Telegram
def deleteMessage(token, chat_id, message_id):
    error_count = 0
    while error_count < 6:
        headers = {'User-Agent': UA}
        url = f'https://tg.nano.ac/bot{token}/deleteMessage'
        params = {'chat_id': chat_id, 'message_id': message_id}
        try:
            response = requests.get(
                url=url, params=params, headers=headers, timeout=(5, 10))
            assert response.status_code == 200
            logger.debug(response.json())
            return
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.warning(e)
            error_count += 1
        time.sleep(5)


def db_insert(x):
    while True:
        try:
            db.insert_one(x)
            break
        except pymongo.errors.DuplicateKeyError:
            break
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.warning(e)


def db_update(x, param):
    while True:
        try:
            return db.find_one_and_update(x, param)
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.warning(e)


def detect():
    # valid means firstpage
    valid_news_urls = set([x['url'] for x in db.find({'valid': True})])
    all_news_urls = set([x['url'] for x in db.find()])

    logger.debug(f'Valid: {len(valid_news_urls)}, All: {len(all_news_urls)}')

    while True:
        insert_news_urls = set()
        delete_news_urls = set()
        try:
            news = []
            news += crawler.detectInfo()
            news += crawler.detectInfoAcademic()
            news += crawler.detectMyhome()
            news += crawler.detectNews()
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/zydt.htm')
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/kgtz.htm')
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/sgwx.htm')
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/fwtz.htm')
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/wgtb.htm')
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/qtkx.htm')
            news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/gjtz.htm')
            news += crawler.detectOffice(
                'http://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=2710')
            news += crawler.detectOffice(
                'http://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=22')
            news += crawler.detectOffice(
                'http://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=3303')

            __news = []
            __news += crawler.detectInfo(True)
            __news += crawler.detectInfoAcademic(True)
            __news += crawler.detectMyhome(True)
            __news += crawler.detectNews(True)
            __news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/zydt.htm', True)
            __news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/kgtz.htm', True)
            __news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/sgwx.htm', True)
            __news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/fwtz.htm', True)
            __news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/wgtb.htm', True)
            __news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/qtkx.htm', True)
            __news += crawler.detectLibrary(
                'https://lib.tsinghua.edu.cn/tzgg/gjtz.htm', True)
            __news += crawler.detectOffice(
                'http://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=2710', True)
            __news += crawler.detectOffice(
                'http://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=22', True)
            __news += crawler.detectOffice(
                'http://xxbg.cic.tsinghua.edu.cn/oath/list.jsp?boardid=3303', True)

        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.error(e)
            time.sleep(60)
            continue

        for x in news:
            if x['url'] not in all_news_urls:

                # Send to Pipeline channel
                sendMessage(config['TOKEN']['fwer'], config['FORWARD']['pipe'],
                            json.dumps({'type': 'newinfo', 'data': x}))

                # Send to THU INFO channel
                msgID = sendMessage(config['TOKEN']['fwer'], config['FORWARD']['channel'],
                                    format.tg_single(x), 'MarkdownV2')

                # Send to thu.closed.social
                try:
                    __msgID = mastodon.toot(format.mastodon(x)).id
                except Exception as e:
                    logger.debug(traceback.format_exc())
                    logger.warning(e)
                    __msgID = -1

                insert_news_urls.add(x['url'])
                x['valid'] = True
                x['deleted'] = False
                x['createTime'] = datetime.now()
                x['msgID'] = {'info_channel': msgID,
                              'notify': 0, 'tuna': 0, 'closed': __msgID}
                db_insert(x)

        news_urls = [x['url'] for x in news]
        __news_urls = [x['url'] for x in news]
        for u in valid_news_urls:
            if u not in news_urls:
                if u in __news_urls:
                    delete_news_urls.add(u)
                    db_update(
                        {'url': u}, {'$set': {'valid': False, 'deleted': False}})
                else:
                    delete_news_urls.add(u)
                    x = db_update(
                        {'url': u}, {'$set': {'valid': False, 'deleted': True}})

                    # Delete from Pipeline channel
                    sendMessage(config['TOKEN']['fwer'], config['FORWARD']['pipe'],
                                json.dumps({'type': 'delinfo', 'data': u}))

                    # Delete from THU INFO channel
                    msgID = x['msgID']['info_channel']
                    if msgID > 0:
                        deleteMessage(config['TOKEN']['fwer'], config['FORWARD']['channel'],
                                      msgID)

                    # Delete from thu.closed.social
                    try:
                        msgID = x['msgID']['closed']
                        if msgID > 0:
                            mastodon.status_delete(msgID)
                    except Exception as e:
                        logger.debug(traceback.format_exc())
                        logger.warning(e)

        all_news_urls.update(insert_news_urls)
        valid_news_urls.update(insert_news_urls)
        valid_news_urls -= delete_news_urls

        if len(insert_news_urls) > 0 or len(delete_news_urls) > 0:
            logger.info('Messages: %d, New: %d, Del: %d' % (
                len(news_urls), len(insert_news_urls), len(delete_news_urls)))

        sendHeartbeat()
        time.sleep(60)


if __name__ == '__main__':
    detect()
