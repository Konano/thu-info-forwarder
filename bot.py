import crawler
import json
import time
import os
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(funcName)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def detect():
    try:
        with open('/data/info.json', 'r') as file:
            lastMessages = json.load(file)
    except:
        lastMessages = []

    while True:
        messages = []
        try:
            category_list = ['academic', '7days', 'business', 'poster', 'research']
            for category in category_list:
                messages += crawler.detect(config['URL'][category])
            messages += crawler.detectBoard(config['URL']['board'])
            messages += crawler.detectLibrary(config['URL']['library'])
        except:
            logging.warning('Network Error')
            time.sleep(60)
            continue

        for each in messages:
            each['title'] = each['title'].replace('[','(').replace(']',')')
            if each['url'][0] == '/':
                each['url'] = config['URL']['postinfo'] + each['url']

        if len(messages) == 0:
            logging.warning('empty messages')
            time.sleep(60)
            continue

        newMessages = []
        delMessages = []

        for each in messages:
            if each not in lastMessages:
                newMessages.append(each)

        for each in lastMessages:
            if each not in messages:
                delMessages.append(each)

        if len(newMessages) > 0 or len(delMessages) > 0:
            logging.info('Messages: %d, New: %d, Del: %d'%(len(messages),len(newMessages),len(delMessages)))
        
        if newMessages != []:
            if len(newMessages) > 3:
                newMessages = newMessages[:3]
            # try:
            #     sendMsg('I'+json.dumps(newMessages))
            # except:
            #     logging.exception('Connect Error')
            #     running = False
            #     return

            # for each in newMessages:
            #     lastMessages.append(each)

        if delMessages != []:
            if len(delMessages) > 3:
                delMessages = delMessages[:3]
            # try:
            #     sendMsg('D'+json.dumps(delMessages))
            # except:
            #     logging.exception('Connect Error')
            #     running = False
            #     return

            # for each in delMessages:
            #     lastMessages.remove(each)

        with open('/data/info.json', 'w') as file:
            json.dump(lastMessages, file)

        time.sleep(60)

if __name__ == '__main__':
    detect()