from pymongo import MongoClient
import logging
from logging import Formatter
from cloghandler import ConcurrentRotatingFileHandler
from hq.Worker import Worker

class HQDaemon:
    def __init__(self, config):
        self.config = config
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
    def loadDb(config):
        client = MongoClient(
            host=config['host'],
            port=int(config['port'])
        )
        return client.__getattr__(config['db'])

    def start(self):
        self.logger.info("[Daemon] Started")
        for i in range(0, int(self.config['daemon']['workers'])):
            worker = Worker(self.config, name="worker_%s" % i)
            self.workers.append(worker)
            worker.start()
            return