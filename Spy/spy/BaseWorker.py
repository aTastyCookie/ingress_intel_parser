import threading
import re
import http.cookiejar
from bs4 import BeautifulSoup
import urllib
import logging
from pymongo import MongoClient
import pika
import json
import time
from spy.exceptions.Ingress import IngressException
from spy.exceptions.AccountBanned import AccountBannedException
from spy.api.intel import Intel
from spy.api.utils import get_field


class BaseWorker(threading.Thread):
    def __init__(self, config, tiles, account, notifier,
                 group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        self.config = config
        self.tiles = tiles
        self.notifier = notifier
        self.account = account
        self.logger = logging.getLogger("daemon")
        client = MongoClient(
            host=config['db']['host'],
            port=int(config['db']['port'])
        )
        self.db = client.__getattr__(config['db']['db'])

        self.headers = [
            (
                'User-Agent',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) ' +
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
            )
        ]
        self.ingress_url = 'http://www.ingress.com/intel'
        self.login_page_url = 'https://accounts.google.com/ServiceLogin?service=grandcentral'
        self.auth_url = 'https://accounts.google.com/ServiceLoginAuth'
        self.cookies = http.cookiejar.CookieJar()
        self.opener = self.buildOpener(self.cookies)
        self.accountCookies = None

        super().__init__(group, target, name, args, kwargs, daemon=daemon)

    def buildOpener(self, cookieJar):
        opener = urllib.request.build_opener()
        opener.addheaders = self.headers
        opener.add_handler(urllib.request.HTTPRedirectHandler())
        opener.add_handler(urllib.request.HTTPSHandler())
        opener.add_handler(urllib.request.HTTPCookieProcessor(cookieJar))
        return opener

    def getUrlContent(self, url):
        return str(self.opener.open(url).read())

    def getLoginCookies(self):
        for cookie in self.cookies:
            if cookie.domain == 'www.ingress.com':
                if cookie.name == 'csrftoken' and cookie.expires > int(time.time()):
                    return self.accountCookies
        email = self.account['email']
        password = self.account['password']
        self.logger.info('[%s] Login' % self.name)
        login_url = re.findall('<a href="(.*?)" class="button_link"', self.getUrlContent(self.ingress_url), re.I)[0]
        ltmpl_shdf = re.findall('ltmpl=(.*?)&shdf=(.*)', login_url, re.I)

        parser = BeautifulSoup(self.getUrlContent(login_url), 'html.parser')
        galx_value = parser.find('input', {'name': 'GALX'})['value']
        params = urllib.parse.urlencode({
            'Email': email,
            'Passwd': password,
            'continue': 'https://appengine.google.com/_ah/conflogin?continue=https://www.ingress.com/intel',
            'GALX': galx_value,
            'signIn': 'Sign in',
            'service': 'ah',
            'shdf': ltmpl_shdf[0][1],
            'ltmpl': ltmpl_shdf[0][0]

        })
        self.opener.open(self.auth_url, params.encode('ascii')).read()
        cookies = ""
        banned = True
        for cookie in self.cookies:
            if cookie.domain == 'www.ingress.com':
                if cookie.name == 'csrftoken':
                    banned = False
                cookies += '%s=%s; ' % (cookie.name, cookie.value)
        self.accountCookies = cookies
        if banned:
            self.db.accounts.update_one(self.account, {'$set': {'status': 'BANNED'}})
            raise AccountBannedException(email)
        return cookies

    def getTileCookies(self, tile):
        return self.getLoginCookies() + "ingress.intelmap.shflt=viz; ingress.intelmap.lat=%s; ingress.intelmap.lng=%s; ingress.intelmap.zoom=%s" % (
            tile['centerLat'], tile['centerLng'], 16
        )

    def lockAccount(self):
        self.db.accounts.update_one(self.account, {'$set': {'status': 'BUSY'}})

    def unlockAccount(self):
        if self.account['status'] == 'BUSY':
            self.db.accounts.update_one(self.account, {'$set': {'status': 'OK'}})

    def buildApi(self, tile):
        return Intel(self.getTileCookies(tile), get_field(tile['centerLng'], tile['centerLat'], 16))

    def emit(self, dump):
        dump['meta'] = {
            'account': self.account['email'],
            'spy_region': 'kaliningradskaya oblast',
            'captured_at': int(time.time())
        }
        # self.db.raw.insert(dump)
        # return # TODO debug stuff
        ampqConn = pika.BlockingConnection(
            pika.ConnectionParameters(self.config['rabbitmq']['host'], self.config['rabbitmq']['port'])
        )
        ampq = ampqConn.channel()
        ampq.queue_declare(queue=self.config['rabbitmq']['queue_key'])
        ampq.basic_publish(exchange='', routing_key=self.config['rabbitmq']['queue_key'], body=json.dumps(dump, ensure_ascii=False))
        ampqConn.close()
