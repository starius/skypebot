# -*- coding: utf-8 -*-

import re
import socks
import socket
import urllib2
from xml.etree.cElementTree import parse, ElementTree, Element, SubElement
from cStringIO import StringIO

import Skype4Py

URL_RE = r'https?://[^\s"\']+'
TITLE_RE = r'<title>\s*([^\n]+)\s*</title>'
ARTICLE_RE = r'\[\[[^\n\[\]]+\]\]'

# comment following lines to get url directly (without tor)
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050) # tor
socket.socket = socks.socksocket

# change user-agent (some sites block urllib2)
headers = {'User-Agent' : 'Mozilla/5.0'}

good = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
good = set(unicode(good, "utf-8"))

replace = unicode("—- –-", "utf-8")

WIKIS = (
    'http://urbanculture.in/',
    'https://lurkmore.to/',
    'https://ru.wikipedia.org/wiki/',
)

def get_html(res):
    html = res.read()
    encoding = ''
    if 'charset=' in res.headers['content-type']:
        encoding = res.headers['content-type'].split('charset=')[-1]
        html = unicode(html, encoding)
    for from_to in replace.split():
        f = from_to[0]
        t = from_to[1]
        html = html.replace(f, t)
    html = ''.join(c for c in html if c in good or ord(c) < 128)
    return html

def reply_http_links(Message):
    text = Message.Body
    for url in list(re.findall(URL_RE, text))[:10]:
        if re.match('.+(jpg|jpeg|gif|png)$', url.lower()):
            continue
        try:
            req = urllib2.Request(url, None, headers)
            res = urllib2.urlopen(req)
            html = get_html(res)
            title = ''
            try:
                xml = parse(StringIO(html))
                title = xml.getroot().find('head').find('title').text
            except:
                title = re.search(TITLE_RE, html).groups()[0]
            if title:
                resp = 'URL title: <%s>' % title
                if type(title) == str:
                    title = unicode(title, "utf-8")
                Message.Chat.SendMessage(resp)
        except Exception, e:
            print('error getting ' + url + ' ' + str(e))

def reply_wiki_links(Message):
    text = Message.Body
    for article in list(re.findall(ARTICLE_RE, text))[:10]:
        article = article[2:-2] # strip [[ and ]]
        for wiki in WIKIS:
            url = wiki + article
            req = urllib2.Request(url, None, headers)
            try:
                urllib2.urlopen(req)
                resp = url
                if type(title) == str:
                    title = unicode(title, "utf-8")
                Message.Chat.SendMessage(resp)
                break
            except:
                pass

class MySkypeEvents:
    def MessageStatus(self, Message, Status):
        if Status == Skype4Py.enums.cmsReceived:
            reply_http_links(Message)
            reply_wiki_links(Message)

skype = Skype4Py.Skype(Events=MySkypeEvents())
skype.Attach()

_ = input()

