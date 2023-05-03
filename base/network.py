import functools
import http.cookiejar as HC
import logging

import requests
from requests.exceptions import ConnectTimeout, ReadTimeout, SSLError

from base.debug import eprint
from base.log import logger


class StatusCodeError(Exception):
    pass


def attempt(times: int):
    def decorate(func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except (ConnectTimeout, ReadTimeout, StatusCodeError, SSLError) as e:
                    eprint(e, logging.DEBUG)
                except Exception as e:
                    raise e
            logger.debug(f'{args[0] = }')
            raise Exception(f'Network error in {times} attempts')
        return wrap
    return decorate


@attempt(5)
def get(url: str, timeout=(5, 10), **kwargs):
    resp = requests.get(url, timeout=timeout, **kwargs)
    if resp.status_code != 200:
        raise StatusCodeError(f'{resp.status_code = }, != 200')
    return resp


# ========== session ==========

session = requests.session()
session.cookies = HC.LWPCookieJar(filename='secret/cookies')
try:
    session.cookies.load(ignore_discard=True)
except:
    pass


@attempt(5)
def session_post(url: str, timeout=(5, 10), **kwargs):
    resp = session.post(url, timeout=timeout, **kwargs)
    if resp.status_code != 200:
        raise StatusCodeError(f'{resp.status_code = }, != 200')
    return resp


@attempt(5)
def session_get(url: str, timeout=(5, 10), **kwargs):
    return session.get(url, timeout=timeout, **kwargs)


# @attempt(5)
# def mastodon_toot(mastodon, status, **kwargs):
#     return mastodon.toot(status, **kwargs)
