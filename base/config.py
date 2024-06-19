import configparser

config = configparser.RawConfigParser()
config.read('config.ini')

botToken = config['BOT']['token']
heartbeatURL = config['BOT']['heartbeaturl']
TelegramAPI = config['BOT']['apiurl']

CHANNEL = dict(config.items('CHANNEL'))
MASTODON = dict(config.items('MASTODON'))
