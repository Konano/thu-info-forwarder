import binascii
import re
from urllib.parse import urlparse

from Crypto.Cipher import AES


# MarkdownV2 Mode
def escaped(str):
    return re.sub('([\_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])', '\\\\\\1', str)


def encrypt(url: str) -> str:
    """WebVPN URL encryption"""
    encryStr = b'wrdvpnisthebest!'

    def encrypt(url):
        url = str.encode(url)
        cryptor = AES.new(encryStr, AES.MODE_CFB,
                          encryStr, segment_size=16 * 8)
        return bytes.decode(binascii.b2a_hex(encryStr)) + \
            bytes.decode(binascii.b2a_hex(cryptor.encrypt(url)))

    url = urlparse(url)
    scheme = url.scheme
    host = url.hostname
    port = url.port
    url = url._replace(netloc=url.netloc.split(':', 1)[0])
    path = url.geturl().split(host, 1)[1]
    url = encrypt(host) + path

    if port is not None:
        url = 'https://webvpn.tsinghua.edu.cn/' + scheme + '-' + port + '/' + url
    else:
        url = 'https://webvpn.tsinghua.edu.cn/' + scheme + '/' + url

    return url


# # WebVPN
# def encrypt(url):

#     encryStr = b'wrdvpnisthebest!'

#     def encrypt(url):
#         url = str.encode(url)
#         cryptor = AES.new(encryStr, AES.MODE_CFB, encryStr, segment_size=16*8)

#         return bytes.decode(binascii.b2a_hex(encryStr)) + \
#             bytes.decode(binascii.b2a_hex(cryptor.encrypt(url)))

#     if url[0:7] == 'http://':
#         url = url[7:]
#         protocol = 'http'
#     elif url[0:8] == 'https://':
#         url = url[8:]
#         protocol = 'https'

#     v6 = re.match('[0-9a-fA-F:]+', url)
#     if v6 != None:
#         v6 = v6.group(0)
#         url = url[len(v6):]

#     segments = url.split('?')[0].split(':')
#     port = None
#     if len(segments) > 1:
#         port = segments[1].split('/')[0]
#         url = url[0: len(segments[0])] + url[len(segments[0]) + len(port) + 1:]

#     try:
#         idx = url.index('/')
#         host = url[0: idx]
#         path = url[idx:]
#         if v6 != None:
#             host = v6
#         url = encrypt(host) + path
#     except:
#         if v6 != None:
#             url = v6
#         url = encrypt(url)

#     if port != None:
#         url = 'https://webvpn.tsinghua.edu.cn/' + protocol + '-' + port + '/' + url
#     else:
#         url = 'https://webvpn.tsinghua.edu.cn/' + protocol + '/' + url

#     return url


def telegram(data):
    text = \
        'Info %s' % escaped(data["source"]) + '\n' + \
        '[%s](%s)' % (escaped(data["title"]), data["url"]) + ' ' + \
        '[\\(webvpn\\)](%s)' % encrypt(data["url"])
    return text


def mastodon(data):
    text = '\n'.join([
        '%s - %s' % (data['source'], data['title']),
        '校内: %s' % data['url'],
        '校外: %s' % encrypt(data["url"])
    ])
    return text
