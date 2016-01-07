from spy.BaseWorker import BaseWorker
from time import sleep, time
from random import randint
import math
import spy.api.utils as utils


class Worker(BaseWorker):
    def run(self):
        portals = []
        portalsDetail = {}

        def findPortals(entities):
            for entity in entities:
                if isinstance(entity, list):
                    findPortals(entity)
                elif isinstance(entity, str):
                    if entity.endswith('.16') and entity not in portals:
                        portals.append(entity)

        self.lockAccount()
        chunkSize = 3
        chunks = [self.tiles[x:x + chunkSize] for x in range(0, len(self.tiles), chunkSize)]
        while True:
            for chunk in chunks:
                api = self.buildApi(chunk[0])
                self.logger.info('[%s] Fetch entities' % self.name)
                fetched = api.fetch_map([x['tile'] for x in chunk])
                for tile, entities in fetched['map'].items():
                    findPortals(entities['gameEntities'])
                self.logger.info('[%s] Fetch portals' % self.name)
                for portal in portals:
                    guid = portal.replace('.', '_')
                    portalsDetail[guid] = api.fetch_portal(portal)
                for tile in chunk:
                    data = self.handleTile(tile)
                    portalsInTile = {}
                    data['portals'] = portalsDetail
                    for guid, portal in portalsDetail.items():
                        portalLng = portal[3] / 1E6
                        portalLat = portal[2] / 1E6
                        if portalLat <= tile['bounds']['north'] and portalLat >= tile['bounds']['south'] and \
                                        portalLng <= tile['bounds']['east'] and portalLng >= tile['bounds']['west']:
                            portalsInTile[guid] = portal
                    data['portalsInTile'] = portalsInTile
                    self.emit(data)
            sleeptime = randint(300, 600)
            self.logger.info('[%s] Sleep %s' % (self.name, sleeptime))
            sleep(sleeptime)

    def handleTile(self, tile):
        api = self.buildApi(tile)
        entities = api.fetch_map([tile['tile']])
        self.logger.info('[%s] Fetch score' % self.name)
        score = api.fetch_score()
        self.logger.info('[%s] Fetch region' % self.name)
        region = api.fetch_region()
        self.logger.info('[%s] Fetch comm' % self.name)
        comm = {
            'faction': api.fetch_msg(tab='faction'),
            'alerts': api.fetch_msg(tab='alerts'),
            'all': api.fetch_msg(tab='all'),
        }
        return {
            'tile': tile,
            'entities': entities['map'][tile['tile']]['gameEntities'],
            'region': region,
            'score': score,
            'comm': comm,
        }
