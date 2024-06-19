import time

from mastodon import Mastodon
from mastodon.errors import MastodonNetworkError

from base.config import MASTODON
from base.debug import eprint
from base.log import logger


def init(url, clientcred, **kwargs):
    Mastodon.create_app(f'Telegram', api_base_url=url, to_file=clientcred)


def login(url, email, pwd, clientcred, usercred, **kwargs):
    try:
        mastodon = Mastodon(client_id=clientcred, api_base_url=url)
        mastodon.log_in(username=email, password=pwd, to_file=usercred)
        mastodon = Mastodon(access_token=usercred, api_base_url=url)
    except Exception:
        mastodon = None
        logger.error('Mastodon Login Failed')
    return mastodon


mastodon = None
while mastodon is None:
    try:
        mastodon = login(**MASTODON)
        if mastodon is None:
            init(**MASTODON)
            logger.warning('Login thu.closed.social failed, wait 60s then retry...')
            time.sleep(60)
    except MastodonNetworkError as e:
        logger.warning('MastodonNetworkError, wait 60s then retry...')
        time.sleep(60)
    except Exception as e:
        eprint(e)
        logger.warning('Wait 60s then retry...')
        time.sleep(60)
logger.info('Mastodon login success')
