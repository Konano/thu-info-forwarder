import functools
import http.cookiejar as HC
import logging
from typing import cast

import requests
from requests import Response
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
def get(url: str, timeout=(5, 10), validate_status=True, **kwargs) -> Response:
    resp: Response = requests.get(url, timeout=timeout, **kwargs)
    if validate_status and resp.status_code != 200:
        raise StatusCodeError(f'{resp.status_code = }, != 200')
    return resp


# ========== session ==========
session = requests.session()
session.cookies = HC.LWPCookieJar(filename='secret/cookies')  # type: ignore
try:
    cast(HC.LWPCookieJar, session.cookies).load(ignore_discard=True)
except:
    pass


@attempt(5)
def session_post(url: str, timeout=(5, 10), **kwargs) -> Response:
    resp: Response = session.post(url, timeout=timeout, **kwargs)
    if resp.status_code != 200:
        raise StatusCodeError(f'{resp.status_code = }, != 200')
    return resp


@attempt(5)
def session_get(url: str, timeout=(5, 10), **kwargs) -> Response:
    return session.get(url, timeout=timeout, **kwargs)
