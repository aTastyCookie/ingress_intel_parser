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
from spy.exceptions.AccountExpired import AccountExpiredException
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

        super().__init__(group, target, name, args, kwargs, daemon=daemon)

    def process(self):
        pass

    def run(self):
        try:
            self.process()
        except AccountBannedException:
            self.db.accounts.update_one(self.account, {'$set': {'status': 'BANNED'}})
        except AccountExpiredException:
            self.db.accounts.update_one(self.account, {'$set': {'status': 'EXPIRED'}})

    def getTileCookies(self, tile):
        return "ingress.intelmap.shflt=viz; ingress.intelmap.lat=%s; ingress.intelmap.lng=%s; ingress.intelmap.zoom=%s" % (
            tile['centerLat'], tile['centerLng'], 16
        )

    def lockAccount(self):
        self.db.accounts.update_one(self.account, {'$set': {'status': 'BUSY'}})

    def unlockAccount(self):
        if self.account['status'] == 'BUSY':
            self.db.accounts.update_one(self.account, {'$set': {'status': 'OK'}})

    def buildApi(self, tile):
        return Intel(self.account, get_field(tile['centerLng'], tile['centerLat'], 16, tile=self.getTileCookies(tile)))

    def emit(self, dump):
        dump['meta'] = {
            'account': self.account['_id'],
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
