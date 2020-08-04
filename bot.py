import crawler
import format

import os
import json
import time
import requests
import configparser
from mastodon import Mastodon


config = configparser.ConfigParser()
config.read('config.ini')

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(funcName)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

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


# Send msg to Telegram
def sendMessage(token, text, chat_id, parse_mode=None):
    while True:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'}
        url = f'https://tg.nanoape.workers.dev/bot{token}/sendMessage'
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
        url = f'https://tg.nanoape.workers.dev/bot{token}/deleteMessage'
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
    try:
        with open(config['JSON']['info'], 'r') as file:
            lastMessages = json.load(file)
    except Exception as e:
        logging.error(e)
        lastMessages = {}

    while True:
        messages = []
        try:
            category_list = ['academic', '7days', 'business', 'poster', 'research']
            for category in category_list:
                messages += crawler.detect(config['URL'][category])
            messages += crawler.detectBoard(config['URL']['board'])
            messages += crawler.detectLibrary(config['URL']['library'])
        except Exception as e:
            logging.error(e)
            time.sleep(60)
            continue

        for each in messages:
            each['title'] = each['title'].replace('[','(').replace(']',')')
            if each['url'][0] == '/':
                each['url'] = config['URL']['postinfo'] + each['url']

        newMessages = []
        delMessages = []

        for each in messages:
            if each['url'] not in lastMessages.keys():
                newMessages.append(each)

        messageURLs = [x['url'] for x in messages]

        for each in lastMessages.keys():
            if each not in messageURLs:
                delMessages.append(each)

        if len(newMessages) > 0 or len(delMessages) > 0:
            logging.info('Messages: %d, New: %d, Del: %d' % (len(messages), len(newMessages), len(delMessages)))
        
        if newMessages != []:
            if len(newMessages) > 3:
                newMessages = newMessages[:3]
            for each in newMessages:
                logging.info(each)
                # Send to Pipeline channel
                sendMessage(config['TOKEN']['fwer'], json.dumps({'type': 'newinfo', 'data': each}), config['FORWARD']['pipe'])
                # Send to THU INFO channel
                msgID = sendMessage(config['TOKEN']['fwer'], format.tg_single(each), config['FORWARD']['channel'], 'MarkdownV2')
                # Send to Closed mastodon
                try:
                    mastodon.toot(format.mastodon(each))['id']
                except Exception as e:
                    logging.error(e)
                lastMessages[each['url']] = {'data': each, 'msgid': msgID}

        if delMessages != []:
            if len(delMessages) > 3:
                delMessages = delMessages[:3]
            for each in delMessages:
                logging.info('Delete: '+each)
                # Delete from Pipeline channel
                sendMessage(config['TOKEN']['fwer'], json.dumps({'type': 'delinfo', 'data': each}), config['FORWARD']['pipe'])
                # Delete from THU INFO channel
                deleteMessage(config['TOKEN']['fwer'], config['FORWARD']['channel'], lastMessages[each]['msgid'])
                del lastMessages[each]

        with open(config['JSON']['info'], 'w') as file:
            json.dump(lastMessages, file)

        time.sleep(60)

if __name__ == '__main__':
    detect()