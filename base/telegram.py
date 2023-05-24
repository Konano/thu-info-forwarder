import time

from base import network
from base.debug import eprint
from base.config import TelegramAPI

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'
}


def _request_get(url: str, **kwargs):
    for _ in range(5):
        resp = network.get(url, headers=headers, **kwargs)
        if resp.status_code == 200:
            return resp
        time.sleep(5)
    else:
        raise Exception(
            f'Cloudflare Worker: error with code {resp.status_code}')


def sendMessage(token, chat_id, text, **kwargs):
    """
    Send msg to Telegram
    """
    for _ in range(5):
        url = f'https://{TelegramAPI}/bot{token}/sendMessage'
        params = {'text': text, 'chat_id': chat_id,
                  'disable_web_page_preview': True, **kwargs}
        resp = _request_get(url, params=params)
        if resp.json()['ok'] is False:
            eprint(Exception(resp.json()['description']))
            time.sleep(30)
            continue
        return resp.json()['result']['message_id']
    else:
        raise RuntimeError


def deleteMessage(token, chat_id, message_id, **kwargs):
    """
    Delete msg from Telegram
    """
    url = f'https://{TelegramAPI}/bot{token}/deleteMessage'
    params = {'chat_id': chat_id, 'message_id': message_id, **kwargs}
    _request_get(url, params=params)
