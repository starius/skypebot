# -*- coding: utf-8 -*-

import sys
import datetime
import re
import socket
import urllib2
import httplib2
import random
from xml.etree.cElementTree import parse, ElementTree, Element, SubElement
from cStringIO import StringIO

import Skype4Py

URL_RE = r'https?://[^\s"\']+'
CHARSET_RE = r'charset=([^\s\'\"]+)[\'\"]'
TITLE_RE = r'<title>\s*([^\n]+)\s*</title>'
ARTICLE_RE = r'\[\[[^\n\[\]]+\]\]'
IP_RE = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'

if '--tor' in sys.argv:
    import socks
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
    socket.socket = socks.socksocket

headers = {
    'User-Agent': 'Mozilla/5.0', # change user-agent (some sites block urllib2)
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Language': 'ru,en-US;q=0.8,en;q=0.6',
}

good = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
good = set(unicode(good, "utf-8"))

replace = unicode("—- –-", "utf-8")

WIKIS = {
    'u': ('Urbanculture', 'http://urbanculture.in/'),
    'l': ('Lurkmore', 'https://lurkmore.to/'),
    'rw': ('Русская Википедия', 'https://ru.wikipedia.org/wiki/'),
    'wr': ('Викиреальность', 'http://wikireality.ru/wiki/'),
    'w': ('Wikipedia', 'https://en.wikipedia.org/wiki/'),
}

def get_res(url):
    url = httplib2.iri2uri(url)
    req = urllib2.Request(url, None, headers)
    res = urllib2.urlopen(req)
    return res

def get_html(res):
    html = res.read()
    encoding = ''
    if 'charset=' in res.headers['content-type']:
        encoding = res.headers['content-type'].split('charset=')[-1]
    if not encoding:
        try:
            encoding = re.search(CHARSET_RE, html).groups()[0]
        except:
            pass
    if encoding:
        html = unicode(html, encoding)
    return html

def fix_title(title):
    for from_to in replace.split():
        f = from_to[0]
        t = from_to[1]
        title = title.replace(f, t)
    title = ''.join(c for c in title if c in good or ord(c) < 128)
    return title

def reply_http_links(Message):
    text = Message.Body
    for url in list(re.findall(URL_RE, text))[:10]:
        if re.match('.+(jpg|jpeg|gif|png|pdf)$', url.lower()):
            continue
        print 'Get URL ' + url
        res = get_res(url)
        html = get_html(res)
        title = ''
        try:
            xml = parse(StringIO(html))
            title = xml.getroot().find('head').find('title').text
        except:
            title = re.search(TITLE_RE, html).groups()[0]
        if title:
            Message.Chat.SendMessage('URL title: <%s>' % fix_title(title))

def reply_wiki_links(Message):
    text = Message.Body
    for article in list(re.findall(ARTICLE_RE, text))[:10]:
        article = article[2:-2] # strip [[ and ]]
        article = article.replace(' ', '_')
        resp = ''
        for prefix, (name, url_prefix)  in WIKIS.items():
            prefix = prefix + ':'
            if article.lower().startswith(prefix):
                article = re.sub('^' + prefix, '', article)
                url = url_prefix + article
                resp = True
                break
        if not resp:
            for prefix, (name, url_prefix)  in WIKIS.items():
                url = url_prefix + article
                try:
                    get_res(url)
                    resp = True
                    break
                except:
                    pass
        if resp:
            name = unicode(name, 'utf-8')
            resp = name + ': ' + article.replace('_', ' ') + ' ' + url
            Message.Chat.SendMessage('/me ' + resp)

def reply_smile(Message):
    if random.randint(0, 20) == 0:
        Message.Chat.SendMessage(':3')

def reply_ip(Message):
    text = Message.Body
    for ip in list(re.findall(IP_RE, text))[:10]:
        name = socket.gethostbyaddr(ip)[0]
        Message.Chat.SendMessage(name + ' => ' + ip)


class MySkypeEvents:

    last = datetime.datetime.now()

    def MessageStatus(self, Message, Status):
        if Message.Sender != skype.CurrentUser and Message.Datetime > self.last:
            self.last = Message.Datetime
            reply_http_links(Message)
            reply_wiki_links(Message)
            reply_smile(Message)
            reply_ip(Message)

skype = Skype4Py.Skype(Events=MySkypeEvents())
skype.Attach()

while True:
    _ = input()

