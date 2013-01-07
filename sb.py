# -*- coding: utf-8 -*-

import re
import socks
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

# comment following lines to get url directly (without tor)
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050) # tor
socket.socket = socks.socksocket

headers = {
    'User-Agent': 'Mozilla/5.0', # change user-agent (some sites block urllib2)
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Language': 'ru,en-US;q=0.8,en;q=0.6',
}

good = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
good = set(unicode(good, "utf-8"))

replace = unicode("—- –-", "utf-8")

WIKIS = (
    'http://urbanculture.in/',
    'https://lurkmore.to/',
    'https://ru.wikipedia.org/wiki/',
)

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
        try:
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
        except Exception, e:
            print('error getting ' + url + ' ' + str(e))

def reply_wiki_links(Message):
    text = Message.Body
    for article in list(re.findall(ARTICLE_RE, text))[:10]:
        article = article[2:-2] # strip [[ and ]]
        article = article.replace(' ', '_')
        for wiki in WIKIS:
            url = wiki + article
            try:
                get_res(url)
                Message.Chat.SendMessage(url)
                break
            except:
                pass

def reply_smile(Message):
    if random.randint(0, 20) == 0:
        Message.Chat.SendMessage(':3')

class MySkypeEvents:
    def MessageStatus(self, Message, Status):
        if Status == Skype4Py.enums.cmsReceived:
            reply_http_links(Message)
            reply_wiki_links(Message)
            reply_smile(Message)

skype = Skype4Py.Skype(Events=MySkypeEvents())
skype.Attach()

_ = input()

