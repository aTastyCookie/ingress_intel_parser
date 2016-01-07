import threading
import logging
from pymongo import MongoClient
import pika
import json
from decoders.Portal import Portal
from decoders.Message import Message


class Worker(threading.Thread):
    def __init__(self, config, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        self.config = config
        self.logger = logging.getLogger("daemon")
        client = MongoClient(
            host=config['db']['host'],
            port=int(config['db']['port'])
        )
        self.db = client.__getattr__(config['db']['db'])

        super().__init__(group, target, name, args, kwargs, daemon=daemon)

    def onData(self, ch, method, properties, body):
        data = json.loads(body.decode())
        self.logger.info('[%s] Captured data from %s' % (self.name, data['meta']['spy_region']))
        self.db.raw.insert(data)
        self.db.scores.insert({
            'captured_at': data['meta']['captured_at'],
            'scores': data['score']
        })
        if self.db.regions.count({'regionName': data['region']['regionName']}) == 0:
            self.db.regions.insert(data['region'])
        else:
            self.db.regions.update({'regionName': data['region']['regionName']}, {'$set': data['region']})
        for entity in data['entities']:
            if entity[0].endswith('.b'):  # field
                fieldId = entity[0].replace('.', '_')
                if self.db.fields.count({'id': fieldId}) == 0:
                    self.db.fields.insert({
                        'id': fieldId,
                        'team': entity[2][1],
                        'mu': 0,
                        'portals': [
                            entity[2][2][0][0],
                            entity[2][2][1][0],
                            entity[2][2][2][0]
                        ]
                    })
            elif entity[0].endswith('.9') or \
                    entity[0].endswith('.b_ab') or \
                    entity[0].endswith('.b_bc') or \
                    entity[0].endswith('.b_ac'):  # link
                linkId = entity[0].replace('.', '_')
                if self.db.links.count({'id': linkId}) == 0:
                    self.db.links.insert({
                        'id': linkId,
                        'team': entity[2][1],
                        'portals': [
                            entity[2][2],
                            entity[2][5],
                        ]
                    })

        for guid, portalData in data['portals'].items():
            portalDecoder = Portal()
            portalDetail = portalDecoder.portalDetail(portalData)
            portalDetail['guid'] = guid
            if self.db.portals.count({'guid': guid}) == 0:
                self.db.portals.insert(portalDetail)
            else:
                oldPortalDetail = self.db.portals.find({'guid': guid}).next()
                if oldPortalDetail != portalDetail:
                    portalDetail['history'] = {
                        'timestamp': data['meta']['captured_at'],
                        'previousData': oldPortalDetail
                    }
                    self.db.portals.update({'guid': guid}, {'$set': portalDetail})
        for tab, plexts in data['comm'].items():
            for plext in plexts:
                message = Message.parse(plext)
                if self.db.comm.count({'guid': message['guid']}) == 0:
                    self.db.comm.insert(message)
                if 'MUs' in message['text']:
                    mu = int(message['markup'][4][1]['plain'])
                    if self.db.portals.count({'title': message['markup'][2][1]['name']}) != 0:
                        portal = self.db.portals.find({'title': message['markup'][2][1]['name']}).next()
                        fields = self.db.fields.find(
                            {'portals': {'$elemMatch': {'$eq': portal['guid'].replace('_', '.')}}})
                        for field in fields:
                            field['mu'] += mu
                            self.db.fields.update({'id': field['id']}, {'$set': field})

    def run(self):
        ampqConn = pika.BlockingConnection(
            pika.ConnectionParameters(self.config['rabbitmq']['host'], self.config['rabbitmq']['port'])
        )
        ampq = ampqConn.channel()
        ampq.queue_declare(queue=self.config['rabbitmq']['queue_key'])
        ampq.basic_consume(self.onData, queue=self.config['rabbitmq']['queue_key'],
                           no_ack=True)
        ampq.start_consuming()
        # for i in self.db.raw.find({}, {'_id': False}):
        #     raw = json.dumps(i).encode()
        #     self.onData(None, None, None, raw)
