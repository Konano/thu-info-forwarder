import crawler
import format

import time
import json
import pymongo
import requests
import configparser
from datetime import datetime
from mastodon import Mastodon


config = configparser.ConfigParser()
config.read('config.ini')

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(funcName)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

db = pymongo.MongoClient(f'mongodb://{config["MONGODB"]["user"]}:{config["MONGODB"]["pwd"]}@{config["MONGODB"]["host"]}:{config["MONGODB"]["port"]}/')['service']['info']

# Mastodon.create_app(
#     'bot',
#     api_base_url = config['MASTODON']['url'],
#     to_file = config['MASTODON']['clientcred']
# )
mastodon = Mastodon(
    client_id = config['MASTODON']['clientcred'],
    api_base_url = config['MASTODON']['url']
)
mastodon.log_in(
    username = config['MASTODON']['email'],
    password = config['MASTODON']['pwd'],
    to_file = config['MASTODON']['usercred']
)
mastodon = Mastodon(
    access_token = config['MASTODON']['usercred'],
    api_base_url = config['MASTODON']['url']
)


def sendHeartbeat():
    try:
        requests.get(url=config['HEARTBEAT']['url'], timeout=(5, 10))
    except Exception as e:
        logging.error(e)

# Send msg to Telegram
def sendMessage(token, text, chat_id, parse_mode=None):
    while True:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'}
        url = f'https://tg.nano.ac/bot{token}/sendMessage'
        params = {'text': text, 'chat_id': chat_id, 'disable_web_page_preview': True}
        if parse_mode != None:
            params['parse_mode'] = parse_mode
        try:
            response = requests.get(url=url, params=params, headers=headers, timeout=(5, 10))
            assert response.status_code == 200
            logging.debug(response.json())
            return response.json()['result']['message_id']
        except Exception as e:
            logging.error(e)
            time.sleep(1)
            continue


# Delete msg in Telegram
def deleteMessage(token, chat_id, message_id):
    while True:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'}
        url = f'https://tg.nano.ac/bot{token}/deleteMessage'
        params = {'chat_id': chat_id, 'message_id': message_id}
        try:
            response = requests.get(url=url, params=params, headers=headers, timeout=(5, 10))
            assert response.status_code == 200
            logging.debug(response.json())
            return
        except Exception as e:
            logging.error(e)
            time.sleep(1)
            continue

def detect():
    valid_news_urls = set([x['url'] for x in db.find({'valid': True})])
    all_news_urls = set([x['url'] for x in db.find()])

    logger.debug(f'Valid: {len(valid_news_urls)}, All: {len(all_news_urls)}')

    while True:
        insert_news_urls = set()
        delete_news_urls = set()
        try:
            news = []
            for category in ['academic', '3days', 'business', 'poster', 'research']:
                news += crawler.detect(config['URL'][category])
            
            news += crawler.detectBoard()
            news += crawler.detectLibrary()
            news += crawler.detectMyhome()

            __news = []
            for category in ['academic', '3days', 'business', 'poster', 'research']:
                __news += crawler.detect(config['URL'][category]+'?page=1')

        except Exception as e:
            logging.error(e)
            time.sleep(60)
            continue

        for x in news:
            x['title'] = x['title'].replace('[','(').replace(']',')')
            if x['url'][0] == '/':
                x['url'] = config['URL']['postinfo'] + x['url']

        for x in __news:
            x['title'] = x['title'].replace('[','(').replace(']',')')
            if x['url'][0] == '/':
                x['url'] = config['URL']['postinfo'] + x['url']

        for x in news:
            if x['url'] not in valid_news_urls and x['url'] not in all_news_urls:
                # Send to Pipeline channel
                sendMessage(config['TOKEN']['fwer'], json.dumps({'type': 'newinfo', 'data': x}), config['FORWARD']['pipe'])
                # Send to THU INFO channel
                msgID = sendMessage(config['TOKEN']['fwer'], format.tg_single(x), config['FORWARD']['channel'], 'MarkdownV2')
                # Send to Closed mastodon
                try:
                    __msgID = mastodon.toot(format.mastodon(x)).id
                except Exception as e:
                    __msgID = -1
                    logging.error(e)
                
                insert_news_urls.add(x['url'])
                x['valid'] = True
                x['deleted'] = False
                x['createTime'] = datetime.now()
                x['msgID'] = {'info_channel': msgID, 'notify': 0, 'tuna': 0, 'closed': __msgID}
                db.insert_one(x)
            
        news_urls = [x['url'] for x in news]
        __news_urls = [x['url'] for x in news]
        for u in valid_news_urls:
            if u not in news_urls:
                if u in __news_urls:
                    delete_news_urls.add(u)
                    db.update_one({'url': u}, {'$set': {'valid': False, 'deleted': False}})
                else:
                    delete_news_urls.add(u)
                    x = db.find_one_and_update({'url': u}, {'$set': {'valid': False, 'deleted': True}})

                    # Delete from Pipeline channel
                    sendMessage(config['TOKEN']['fwer'], json.dumps({'type': 'delinfo', 'data': u}), config['FORWARD']['pipe'])
                    # Delete from THU INFO channel
                    msgID = x['msgID']['info_channel']
                    if msgID > 0:
                        deleteMessage(config['TOKEN']['fwer'], config['FORWARD']['channel'], msgID)
                    # Delete from Closed mastodon
                    try:
                        msgID = x['msgID']['closed']
                        if msgID > 0:
                            mastodon.status_delete(msgID)
                    except Exception as e:
                        logging.error(e)
        
        all_news_urls.update(insert_news_urls)
        valid_news_urls.update(insert_news_urls)
        valid_news_urls -= delete_news_urls

        if len(insert_news_urls) > 0 or len(delete_news_urls) > 0:
            logging.info('Messages: %d, New: %d, Del: %d' % (len(news_urls), len(insert_news_urls), len(delete_news_urls)))

        sendHeartbeat()
        time.sleep(60)

if __name__ == '__main__':
    detect()
