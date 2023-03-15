import configparser

config = configparser.RawConfigParser()
config.read('config.ini')

botToken = config['BOT']['token']
heartbeatURL = config['BOT']['heartbeaturl']
TelegramAPI = config['BOT']['apiurl']

MASTODON = config._sections['MASTODON']
CHANNEL = config._sections['CHANNEL']
