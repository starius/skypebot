# -*- coding: utf-8 -*-

import sys
import os
import datetime
import time
import thread
import re
import socket
import urllib2
import httplib2
import random
from xml.etree.cElementTree import parse, ElementTree, Element, SubElement
from cStringIO import StringIO
import HTMLParser

import Skype4Py
import bitly

IRC_ENABLED = True
try:
    from ircbot import SingleServerIRCBot
except:
    IRC_ENABLED = False

URL_RE = r'\b(https?://|www\.)[^\s"\']+'
CHARSET_RE = r'charset=([^\s\'\"]+)[\'\"]'
TITLE_RE = r'<title>\s*(.+)\s*</title>'
TITLE_RE2 = re.compile(r'</title>', re.I)
ARTICLE_RE = (
    r'\[\[([^\n\[\]]+)\]\]',
    r'^! (.+)',
)
IP_RE = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'

CHANGES_TEMPLATE = '/api.php?action=query&list=recentchanges&' +\
    'rcprop=timestamp%7Ctitle%7Cids%7Csizes%7Cflags%7Cuser%7Ccomment&format=xml'

UC_CHANGES = 'http://urbanculture.in' + CHANGES_TEMPLATE
LURK_CHANGES = 'http://lurkmore.to' + CHANGES_TEMPLATE

MWDATEFMT = '%Y-%m-%dT%H:%M:%SZ'

CHANGES_INTERVAL = 60 # seconds

MAX_TITLE_LENGTH = 175
SEPARATORS = [' ']

SHORT_HELP_LIMIT = datetime.timedelta(minutes=2)
FULL_HELP_LIMIT = datetime.timedelta(minutes=10)

WHOIS_URL = 'https://apps.db.ripe.net/whois/search.xml?source=ripe&query-string='

IRC_SERVER = 'irc.freenode.net'
IRC_PORT = 6667
IRC_NICKNAME = 'UC-chan'
IRC_CHANNEL = '#urbanculture'

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
    (('images', 'картинки'),
        "Google Images", 'https://encrypted.google.com/search?tbm=isch&q='),
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

WIKIS_2 = [(['!' + w for w in ww], descr, url) for (ww, descr, url) in WIKIS]

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

BB = (
    ('bb', 10),
    ('cu', 5),
    ('cya', 3),
    ('o_O', 7),
    ('\o/', 10),
    ('-1', 10),
    ('chat--', 10),
    ('лети птичка', 10),
    ('gg', 5),
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

KEY_WORDS = (
    ur'i2p',
    ur'\bтор\b',
    ur'\btor\b',
    ur'цензур',
    ur'реестр',
    ur'лурк',
    ur'lurk',
    ur'google',
    ur'гугл',
    ur'c\+\+',
    ur'с\+\+',
    ur'копирайт',
    ur'пират',
    ur'уязвимост',
    ur'взлом',
    ur'python',
    ur'питон',
    ur'Linux',
    ur'линукс',
    ur'линус',
    ur'linus',
    ur'скайп',
    ur'skype',
    ur'microsoft',
    ur'irc',
    ur'порн',
    ur'porn',
    ur'прон',
    ur'pron',
    ur'urban',
    ur'4pda',
)

BAD_TITLES = (
    u'Обсуждение',
    u'Участник',
    u'Рубрика',
    u'Файл',
    u'commentadmin',
    u'Категория',
)

HELPS = (
    u'help',
    u'помощь',
    u'-h',
    u'--help',
    u'справка',
)

HELP_SHORT = '''
Привет, я UC-тян! Для справки введи help или открой http://pastebin.com/61yq4TwE
'''

HELP_FULL_TEMPLATE = HELP_SHORT + '''
Ссылка на статью в вики или другом сайте: имя_вики статья
    !lurk Рей
    !uc Катя Гордон
    !рувики Русский мат
    !enwiki bitcoin
     ...
Полный список генераторов ссылок:
    %(gen)s

Ссылки на статьи можно кидать без указания вики-проекта,
тогда я буду перебирать проекты по порядку и выдам
ссылку на первый вики-проект, в котором есть такая статья.

Ссылки на статьи можно оформлять в вики-разметке:
    А чо, [[УМВР]]
    Как пропатчить KDE2 под [[FreeBSD]]
    Любой нормальный анимешник должен хотя бы раз посмотреть [[lm:Евангелион]]
     ...

Для получения случайной статьи в данной вики:
    uc случайная

Кидай сюда ссылки, я буду писать, что в них находится.

Если введешь IP-адрес, я выведу немного информации о нем.

Чтобы получить ссылки на последние интересные статьи с хабра, напиши "хабр"

Чтобы получать интересные статьи с хабра, напиши "+habr", отключить "-habr"

Чтобы получать новые правки с urbanculture или лурка,
напиши "+uc" или "+lurk", чтобы отключить "-uc" или "-lurk"
'''

gen = ' '.join(w[0][0] for w in WIKIS)

HELP_FULL = HELP_FULL_TEMPLATE % {'gen': gen}

def u(s):
    if type(s) == str:
        return unicode(s, 'utf-8')
    else:
        return s

def now():
    return datetime.datetime.now()

def get_res(url):
    print 'Get URL ' + url
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

html_parser = HTMLParser.HTMLParser()

def shorten(url):
    url = httplib2.iri2uri(url)
    if BITLY_USERNAME and BITLY_KEY:
        if len(url) > 40 or ':' in url:
            url = bitly.Api(login=BITLY_USERNAME, apikey=BITLY_KEY).shorten(url)
    return url

def fix_title(title):
    title = u(html_parser.unescape(title))
    title = title[:MAX_TITLE_LENGTH]
    return title

def reply_http_links(self):
    text = self.text
    for url in list(re.finditer(URL_RE, text))[:10]:
        url =  url.group()
        if re.match('.+(jpg|jpeg|gif|png|pdf)$', url.lower()):
            continue
        if not url.startswith('http'):
            url = 'http://' + url
        res = get_res(url)
        html = get_html(res)
        title = ''
        try:
            xml = parse(StringIO(html.encode('utf-8')))
            try:
                title = xml.getroot().find('head').find('title').text
            except:
                title = xml.getroot().find('HEAD').find('TITLE').text
            title = u(title)
        except:
            title = re.search(TITLE_RE, html, re.DOTALL|re.I).groups()[0]
            title = re.split(TITLE_RE2, title)[0]
            title = re.sub(r'\s+', ' ', title)
        if title:
            short_url = shorten(url)
            if short_url == url:
                short_url = ''
            self.send('URL title: <%s> %s' % (fix_title(title), short_url))

def prepare_wiki_resp(name, article, url):
    name = unicode(name, 'utf-8')
    article = article.replace('_', ' ').strip()
    if not article:
        return ""
    if '#' in url:
        url_hash = url.split('#', 1)[-1]
        url_hash = httplib2.iri2uri(url_hash)
        url_hash = url_hash.replace(' ', '_').replace('%', '.')
        print url_hash
        url = url.split('#', 1)[0] + '#' + url_hash
    url = url.replace(' ', '%20')
    url = shorten(url)
    resp = name + ': ' + article + ' ' + url
    return '/me ' + resp

def get_wiki_prefix_resp(article, wikis):
    article = u(article)
    for prefixs, name, url_prefix  in wikis:
        for prefix in prefixs:
            for sep in SEPARATORS:
                prefix1 = u(prefix + sep)
                if article.lower().startswith(prefix1.lower()):
                    article = article[len(prefix1):]
                    article = article.strip()
                    if article.lower() in RANDOM:
                        article = 'Special:Random'
                    url = url_prefix + article
                    return prepare_wiki_resp(name, article, url)

def get_wiki_resp(article):
    article = article.split(u'|')[0].strip()
    resp = get_wiki_prefix_resp(article, WIKIS)
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
    resp = get_wiki_prefix_resp(text.strip(), WIKIS_2)
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
    K = 20
    text = self.text
    for bot in BOT:
        if bot in text.lower():
            K = 3
    if random.randint(0, K) == 0:
        smile = weighted_choice(SMILES)
        self.send(smile)

def fc(xml_node, attr_name, attr_value):
    result = []
    for child in xml_node:
        if child.get(attr_name) == attr_value:
            result.append(child)
    return result

def reply_ip(self):
    text = self.text
    for ip in list(re.findall(IP_RE, text))[:10]:
        try:
            name = socket.gethostbyaddr(ip)[0]
        except:
            name = ip
        try:
            url = WHOIS_URL + ip
            xml = parse(get_res(url))
            whois = xml.getroot()
            assert whois.tag == 'whois-resources'
            objects = whois.find('objects')
            country = fc(fc(objects, "type", "inetnum")[0].find('attributes'),
                    "name", "country")[0].get("value")
            addr_objects = fc(objects, "type", "person") +\
                    fc(objects, "type", "role")
            addr = ', '.join(attr.get('value') for attr in \
                    fc(addr_objects[0].find('attributes'), "name", "address"))
            descr = ', '.join(attr.get('value') for attr in \
                    fc(fc(objects, "type", "inetnum")[0].find('attributes'),
                    "name", "descr"))
            route = fc(fc(objects, "type", "route")[0].find('attributes'),
                    "name", "route")[0].get("value")
            self.send("%s (%s): %s; %s; %s [Net: %s]" %
                    (name, ip, country, addr, descr, route))
        except:
            self.send("%s (%s)" % (name, ip))

def short_help(self):
    if self.helps['short'] < now() - SHORT_HELP_LIMIT:
        self.helps['short'] = now()
        self.send(HELP_SHORT)

def full_help(self):
    if self.helps['full'] < now() - FULL_HELP_LIMIT:
        self.helps['full'] = now()
        self.send(HELP_FULL)

def reply_help(self):
    text = self.text
    full = False
    for help in HELPS:
        if text == help or text[1:] == help:
            full = True
            break
    if full:
        full_help(self)
        return

def is_good_looking(txt):
    txt = txt.lower()
    for pattern in KEY_WORDS:
        if re.search(pattern, txt):
            return True
    return False

habr_announces = set()

def reply_habr(self):
    text = self.text
    if text == u'+habr':
        habr_announces.add(self.send)
    if text == u'-habr':
        habr_announces.remove(self.send)

url2announces = {}
url2announces[UC_CHANGES] = set()
url2announces[LURK_CHANGES] = set()

def reply_changes(self):
    text = self.text
    if text == u'+uc':
        url2announces[UC_CHANGES].add(self.send)
    if text == u'-uc':
        url2announces[UC_CHANGES].remove(self.send)
    if text == u'+lurk':
        url2announces[LURK_CHANGES].add(self.send)
    if text == u'-lurk':
        url2announces[LURK_CHANGES].remove(self.send)

def test_change(change):
    title = change.get('title')
    typ = change.get('type')
    delta = int(change.get('newlen')) - int(change.get('oldlen'))
    for bad in BAD_TITLES:
        if bad in title:
            return False
    return typ != 'edit' or abs(delta) > 500

last_check = datetime.datetime.utcnow()

def get_changes():
    lc = globals()['last_check']
    globals()['last_check'] = datetime.datetime.utcnow()
    for changes_url, announces in url2announces.items():
        if not announces:
            continue
        url = changes_url
        url += '&rcend=' + lc.strftime(MWDATEFMT)
        xml = parse(get_res(url))
        api = xml.getroot()
        assert api.tag == 'api'
        changes = api.find('query').find('recentchanges')
        for change in changes:
            assert change.tag == 'rc'
            if test_change(change):
                user = change.get('user')
                typ = change.get('type')
                title = change.get('title')
                diff = change.get('revid')
                comment = change.get('comment')
                delta = int(change.get('newlen')) - int(change.get('oldlen'))
                base_url = changes_url.split('api.php')[0]
                user_page = shorten(base_url + 'Special:Contributions/' + u(user))
                if diff == '0':
                    diff_page = shorten(base_url + title)
                else:
                    diff_page = shorten(base_url + '?diff=' + diff)
                text = '/me ' + typ + ' ' + diff_page + ' ' + title + ' :: ' + \
                        user
                if user != '127.0.0.1':
                    text += ' ' + user_page
                if delta:
                    text += ' :: '
                    if delta > 0:
                        text += '+'
                    text += str(delta)
                if comment:
                    text += ' :: ' + comment
                for announce in announces:
                    announce(text)

last_habr = 0

def get_habr():
    if habr_announces:
        lb = globals()['last_habr']
        new_lb = lb
        xml = parse(get_res('http://habrahabr.ru/rss/hubs/'))
        rss = xml.getroot()
        assert rss.tag == 'rss'
        channel = rss.find('channel')
        message = u""
        for item in channel:
            if item.tag == 'item':
                txt = ''
                for e in item:
                    txt += e.text
                if is_good_looking(txt):
                    link = item.find('link').text
                    title = item.find('title').text
                    title = title.replace('<![CDATA[', '').replace(']]>', '')
                    title = title.strip()
                    number = int(re.search("(\d+)", link).group())
                    if number > lb:
                        new_lb = max(number, new_lb)
                        if lb != 0:
                            message += link + " " + title + "\n"
        globals()['last_habr'] = new_lb
        if message:
            for announce in habr_announces:
                announce(message)

def treat_message(self):
    reply_http_links(self)
    reply_wiki_links(self)
    reply_smile(self)
    reply_ip(self)
    reply_help(self)
    reply_habr(self)
    reply_changes(self)

def new_helps():
    return {'short': now() - SHORT_HELP_LIMIT,
            'full': now() - FULL_HELP_LIMIT}

class SkypeLogger(object):
    def __init__(self):
        self.skype_log_file = None
        self.skype_log_last = now()
        self.last_phrase = ''

    def skype_log(self, Message):
        if not Message.Body:
            return
        if Message.Body == self.last_phrase:
            return
        self.last_phrase = Message.Body
        if self.skype_log_file is None or now().day != self.skype_log_last.day:
            self.skype_log_last = now()
            if self.skype_log_file:
                self.skype_log_file.close()
            date = self.skype_log_last.date().isoformat()
            self.skype_log_file = open(date + ".log", 'a')
        date = ("%s" % now()).split(".")[0]
        who = Message.FromDisplayName + '(' + u(Message.FromHandle) + ')'
        text = date + " " + who + ": " + u(Message.Body)
        self.skype_log_file.write(text.encode('utf-8') + "\n")
        self.skype_log_file.flush()

skype_logger = SkypeLogger()

class SkypeMessage(object):
    pass

chat2send = {}

def send_function(Chat):
    def send(txt):
        Chat.SendMessage(u(txt))
    if Chat not in chat2send:
        chat2send[Chat] = send
    return chat2send[Chat]

class MySkypeEvents:

    last = now()
    chat2len = {}
    chat2help = {}

    def ChatMembersChanged(self, Chat, Message):
        try:
            if Chat in self.chat2len:
                m = SkypeMessage()
                m.send = send_function(Chat)
                if Chat not in self.chat2help:
                    self.chat2help[Chat] = new_helps()
                m.helps = self.chat2help[Chat]
                if len(Chat.Members) > self.chat2len[Chat]:
                    short_help(m)
                elif len(Chat.Members) < self.chat2len[Chat]:
                    bb = weighted_choice(BB)
                    m.send(bb)
            self.chat2len[Chat] = len(Chat.Members)
        except:
            print("Skype - members changed error")

    def MessageStatus(self, Message, Status):
        try:
            Chat = Message.Chat
            self.chat2len[Chat] = len(Chat.Members)
            if Message.Datetime > self.last:
                if Status.startswith('SENT') or Status.startswith('RECEIVED'):
                    skype_logger.skype_log(Message)
                if Message.Sender != skype.CurrentUser:
                    self.last = Message.Datetime
                    m = SkypeMessage()
                    m.text = Message.Body
                    m.send = send_function(Chat)
                    if Chat not in self.chat2help:
                        self.chat2help[Chat] = new_helps()
                    m.helps = self.chat2help[Chat]
                    treat_message(m)
        except:
            print("Skype - message error")

def loop_changes():
    while True:
        try:
            get_changes()
        except:
            print("Error getting changes")
        try:
            get_habr()
        except:
            print("Error getting habr")
        time.sleep(CHANGES_INTERVAL)

thread.start_new_thread(loop_changes, ())

skype = Skype4Py.Skype(Events=MySkypeEvents())
skype.Attach()
for Chat in skype.RecentChats:
    if len(Chat.Members) > 2:
        url2announces[UC_CHANGES].add(send_function(Chat))
        habr_announces.add(send_function(Chat))

if IRC_ENABLED:
    class IrcMessage(object):
        pass

    class TestBot(SingleServerIRCBot):
        def __init__(self, channel, nick, server, port=6667):
            def send(txt):
                for m in txt.split('\n')[:3]:
                    m = u(m).encode('utf8')
                    if m.lower().startswith("/me"):
                        self.connection.action(IRC_CHANNEL, m[4:])
                    else:
                        self.connection.privmsg(IRC_CHANNEL, m)
            SingleServerIRCBot.__init__(self, [(server, port)], nick, nick)
            self.channel = channel
            self.send = send
            self.helps = new_helps()

        def on_welcome(self, c, e):
            c.join(self.channel)

        def on_pubmsg(self, c, e):
            try:
                m = IrcMessage()
                m.text = u(e.arguments()[0])
                m.send = self.send
                m.helps = self.helps
                treat_message(m)
            except:
                print("Irc message error")

    def thread_irc_bot():
        bot = TestBot(IRC_CHANNEL, IRC_NICKNAME, IRC_SERVER, IRC_PORT)
        url2announces[UC_CHANGES].add(bot.send)
        habr_announces.add(bot.send)
        bot.start()
    thread.start_new_thread(thread_irc_bot, ())

class PrintMessage(object):
    def send(self, text):
        print u(text).encode('utf-8')

while True:
    try:
        m = PrintMessage()
        m.text = u(raw_input())
        m.helps = new_helps()
        treat_message(m)
    except KeyboardInterrupt:
        break
    except:
        print 'error'

