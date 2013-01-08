# -*- coding: utf-8 -*-

import sys
import os
import datetime
import re
import socket
import urllib2
import httplib2
import random
from xml.etree.cElementTree import parse, ElementTree, Element, SubElement
from cStringIO import StringIO

import Skype4Py
import bitly

URL_RE = r'\b(https?://|www\.)[^\s"\']+'
CHARSET_RE = r'charset=([^\s\'\"]+)[\'\"]'
TITLE_RE = r'<title>\s*(.+)\s*</title>'
TITLE_RE2 = re.compile(r'</title>', re.I)
ARTICLE_RE = (
    r'\[\[([^\n\[\]]+)\]\]',
    r'^! (.+)',
)
IP_RE = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'

if '--tor' in sys.argv:
    import socks
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
    socket.socket = socks.socksocket

BITLY_USERNAME = os.environ.get('BITLY_USERNAME')
BITLY_KEY = os.environ.get('BITLY_KEY')

headers = {
    'User-Agent': 'Mozilla/5.0', # change user-agent (some sites block urllib2)
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Language': 'ru,en-US;q=0.8,en;q=0.6',
}

good = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
good = set(unicode(good, "utf-8"))

replace = (
    ("—", "-"),
    ("–", "-"),
    ("‒", "-"),
    ("―", "-"),
    ("⁓", "~"),
    ("&ndash;", "-"),
    ("&mdash;", "-"),
    ("&#x2012;", "-"),
    ("&#x2013;", "-"),
    ("&#x2014;", "-"),
    ("&#x2015;", "-"),
    ("&#x2053;", "-"),
    ("&#8210;", "-"),
    ("&#8211;", "-"),
    ("&#8212;", "-"),
    ("&#8213;", "-"),
    ("&#8275;", "-"),
)

WIKIS = (
    (('uc', 'калча', 'ук', 'urbanculture'),
        'Urbanculture', 'http://urbanculture.in/'),
    (('l', 'lm', 'лурк', 'лурка', 'лурочка', 'Луркоморье', 'lurk', 'lurka'),
        'Lurkmore', 'https://lurkmore.to/'),
    (('rw', 'вики', 'рв', 'рувики', 'википедия'),
        'Русская Википедия', 'https://ru.wikipedia.org/wiki/'),
    (('wr', 'вр', 'викиреальность'),
        'Викиреальность', 'http://wikireality.ru/wiki/'),
    (('w', 'wiki', 'enwiki', 'wikipedia'),
        'Wikipedia', 'https://en.wikipedia.org/wiki/'),
    (('google', 'ggg', 'гугл', 'гугол', 'гуголь'),
        "Google I'm Feeling Lucky", 'http://www.google.com/search?btnI&q='),
    (('yandex', 'ya', 'яндекс'), "Yandex", 'http://yandex.ru/yandsearch?text='),
    (('lmgtfy', 'lg'), "Let me google that for you", 'http://lmgtfy.com/?q='),
    (('ud', 'urbandictionary'),
        "Urban Dictionary", 'http://www.urbandictionary.com/define.php?term='),
    (('gt', 'translate'), "Google Tranlate",
        'http://translate.google.com/#auto|ru|'),
    (('mt', 'multitran'), "Multitran", 'http://www.multitran.ru/c/m.exe?s='),
    (('webster', ), "Free Merriam-Webster Dictionary",
        'http://www.merriam-webster.com/dictionary/')
)

SMILES = (
    (':3', 10),
    (':)', 10),
    (';)', 3),
    ('o_O', 7),
    (':/', 3),
    (':\\', 3),
    (':|', 5),
    ('XD', 2),
    (':p', 10),
    (':D', 5),
    (':]', 4),
    (':*', 4),
    ('|-)', 4),
    ('^_^', 7),
    ('^__^', 5),
    ('>:3', 2),
    ('8)', 2),
    (";'-)", 3),
    ("(_|_)", 1),
    ("o/", 6),
    ("(mooning)", 1),
    ("(drunk)", 2),
    ("(facepalm)", 2),
)

RANDOM = (
    u'случайная',
    u'случайный',
    u'случайное',
    u'рандом',
    u'random',
    u'рандомная',
)

BOT = (
    u'bot',
    u'бот',
    u'ссылк',
    u'зузя',
    u'зузи',
    u'зюзи',
    u'зюзя',
    u'zuzi',
    u'uc-т',
    u'uc-chan',
)

def u(s):
    if type(s) == str:
        return unicode(s, 'utf-8')
    else:
        return s

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
    for f, t in replace:
        f = unicode(f, 'utf-8')
        t = unicode(t, 'utf-8')
        title = title.replace(f, t)
    title = ''.join(c for c in title if c in good or ord(c) < 128)
    return title

def reply_http_links(self):
    text = self.text
    for url in list(re.finditer(URL_RE, text))[:10]:
        url =  url.group()
        if re.match('.+(jpg|jpeg|gif|png|pdf)$', url.lower()):
            continue
        if not url.startswith('http'):
            url = 'http://' + url
        print 'Get URL ' + url
        res = get_res(url)
        html = get_html(res)
        title = ''
        try:
            xml = parse(StringIO(html))
            title = xml.getroot().find('head').find('title').text
        except:
            title = re.search(TITLE_RE, html, re.DOTALL).groups()[0]
            title = re.split(TITLE_RE2, title)[0]
            title = re.sub(r'\s+', ' ', title)
        if title:
            self.send('URL title: <%s>' % fix_title(title))

def prepare_wiki_resp(name, article, url):
    name = unicode(name, 'utf-8')
    article = article.replace('_', ' ')
    url = url.replace(' ', '%20')
    url = httplib2.iri2uri(url)
    if len(url) > 40 and BITLY_USERNAME and BITLY_KEY:
        url = bitly.Api(login=BITLY_USERNAME, apikey=BITLY_KEY).shorten(url)
    resp = name + ': ' + article + ' ' + url
    return '/me ' + resp

def get_wiki_prefix_resp(article):
    article = u(article)
    for prefixs, name, url_prefix  in WIKIS:
        for prefix in prefixs:
            for sep in [' ', ':']:
                prefix1 = u(prefix + sep)
                if article.lower().startswith(prefix1.lower()):
                    article = article[len(prefix1):]
                    article = article.strip()
                    if article.lower() in RANDOM:
                        article = 'Special:Random'
                    url = url_prefix + article
                    return prepare_wiki_resp(name, article, url)

def get_wiki_resp(article):
    article = article.strip()
    resp = get_wiki_prefix_resp(article)
    if resp:
        return resp
    for prefixs, name, url_prefix  in WIKIS:
        url = url_prefix + article
        try:
            print 'Try ' + url
            get_res(url)
            return prepare_wiki_resp(name, article, url)
        except:
            pass

def reply_wiki_links(self):
    text = self.text
    resp = get_wiki_prefix_resp(text.strip())
    if resp:
        self.send(resp)
        return
    articles = []
    for a_re in ARTICLE_RE:
        a_re = unicode(a_re, 'utf-8')
        articles += re.findall(a_re, text)
    for article in articles[:10]:
        resp = get_wiki_resp(article)
        if resp:
            self.send(resp)

def weighted_choice(s):
    return random.choice(sum(([v]*wt for v,wt in s),[]))

def reply_smile(self):
    K = 15
    text = self.text
    for bot in BOT:
        if bot in text.lower():
            K = 3
    if random.randint(0, K) == 0:
        smile = weighted_choice(SMILES)
        self.send(smile)

def reply_ip(self):
    text = self.text
    for ip in list(re.findall(IP_RE, text))[:10]:
        name = socket.gethostbyaddr(ip)[0]
        self.send(name + ' => ' + ip)

def treat_message(self):
    reply_http_links(self)
    reply_wiki_links(self)
    reply_smile(self)
    reply_ip(self)

class SkypeMessage(object):
    pass

class MySkypeEvents:

    last = datetime.datetime.now()

    def MessageStatus(self, Message, Status):
        if Message.Sender != skype.CurrentUser and Message.Datetime > self.last:
            self.last = Message.Datetime
            m = SkypeMessage()
            m.text = Message.Body
            m.send = Message.Chat.SendMessage
            treat_message(m)

skype = Skype4Py.Skype(Events=MySkypeEvents())
skype.Attach()

while True:
    _ = raw_input()

