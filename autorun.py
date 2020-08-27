import os
import sys
import time
import json
import requests
import subprocess
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

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
 
class AutoRun():
    def __init__(self, interval, pyfile):
        self.interval = interval
        self.pyfile = pyfile
        self.p = None
 
        self.run()
 
        try:
            while True:
                time.sleep(interval)
                self.poll = self.p.poll()
                if self.poll is not None:
                    
                    # connect to 

                    print('restart...')
                    self.run()
        except KeyboardInterrupt as e:
            print('kill...')
            self.p.kill()
 
    def run(self):
        self.p = subprocess.Popen(['python3', self.pyfile], stdin = sys.stdin, stdout = sys.stdout, stderr = sys.stderr, shell = False)

if __name__ == '__main__':
    # app = AutoRun(config['AUTORUN'].getint('interval'), config['AUTORUN']['pyfile'])
    pass
