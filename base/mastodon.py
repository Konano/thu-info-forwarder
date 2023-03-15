from base.log import logger
from mastodon import Mastodon


def mastodon_init(url, clientcred, **kwargs):
    Mastodon.create_app(f'Telegram', api_base_url=url, to_file=clientcred)


def mastodon_login(url, email, pwd, clientcred, usercred, **kwargs):
    try:
        mastodon = Mastodon(client_id=clientcred, api_base_url=url)
        mastodon.log_in(username=email, password=pwd, to_file=usercred)
        mastodon = Mastodon(access_token=usercred, api_base_url=url)
    except Exception:
        mastodon = None
        logger.error('Mastodon Login Failed')
    return mastodon
