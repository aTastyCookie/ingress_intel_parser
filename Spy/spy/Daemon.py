from pymongo import MongoClient
import logging
from logging import Formatter
from cloghandler import ConcurrentRotatingFileHandler
from spy.Notifier import MailNotifier
from spy.Tilier import Tilier
from spy.Worker import Worker


class SPYDaemon:
    def __init__(self, config):
        self.config = config
        self.notifier = self.loadNotifier(config['notifier'])
        self.db = self.loadDb(config['db'])
        self.configureLogging()
        self.workers = []


    def configureLogging(self):
        logging.root.setLevel(logging.INFO)
        logging.getLogger("requests").setLevel(logging.WARNING)
        self.logger = self.addLogHandler(
            ConcurrentRotatingFileHandler(
                self.config["dirs"]["logs"] + "/daemon.log",
                backupCount=5,
                maxBytes=1024 * 1024 * 5
            ),
            logging.INFO,
            "daemon"
        )

    def addLogHandler(self, handler, level, logger=None):
        handler.setFormatter(Formatter('%(levelname)s: %(asctime)-15s %(message)s'))
        handler.setLevel(level)
        _logger = logging.getLogger(logger)
        _logger.addHandler(handler)
        return _logger

    @staticmethod
    def loadNotifier(config):
        return MailNotifier(
            config['alert_email'],
            config['sandbox'],
            config['apikey']
        )

    @staticmethod
    def loadDb(config):
        client = MongoClient(
            host=config['host'],
            port=int(config['port'])
        )
        return client.__getattr__(config['db'])

    def start(self):
        self.logger.info("[Daemon] Started")
        tiles = Tilier(self.config['tilier']).getTiles()
        self.db.accounts.update_many({'status': 'BUSY'}, {'$set': {'status': 'OK'}})
        accounts = self.db.accounts.find({'status': 'OK'})
        if accounts.count() < 1:
            raise Exception('0 accounts available')
        chunkSize = min(int(len(tiles) / accounts.count()), self.config['daemon']['max_tiles_per_worker'])
        chunks = [tiles[x:x + chunkSize] for x in range(0, len(tiles), chunkSize)]
        for chunk in chunks:
            try:
                account = accounts.next()
                worker = Worker(self.config, chunk, account, self.notifier, name=account['email'])
                self.logger.info("[Daemon] %s worker started" % account['email'])
                worker.start()
                self.workers.append(worker)
            except StopIteration:
                self.logger.warning("[Daemon] Not enough accounts")
                self.notifier.send(
                    'Not enough accounts',
                    'Not enough accounts to work in full power. %s need.' % (len(chunks) - len(self.workers))
                )
