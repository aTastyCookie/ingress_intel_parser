import requests
import re
import json
import time

from spy.exceptions.AccountBanned import AccountBannedException
from spy.exceptions.AccountExpired import AccountExpiredException


class Intel(object):
    def __init__(self, account, field, tile=None):
        self.account = account
        self.check_account()
        self.cookies = self.account['cookies']
        if tile:
            self.cookies += tile
        try:
            token = re.findall(r'csrftoken=(\w*);', self.cookies)[0]
        except:
            raise AccountBannedException(self.account['_id'])
        self.headers = {
            'accept-encoding': 'gzip, deflate',
            'content-type': 'application/json; charset=UTF-8',
            'cookie': self.cookies,
            'origin': 'https://www.ingress.com',
            'referer': 'https://www.ingress.com/intel',
            'user-agent': 'Mozilla/5.0 (MSIE 9.0; Windows NT 6.1; Trident/5.0)',
            'x-csrftoken': token,
        }
        self.field = {
            'maxLatE6': field['maxLatE6'],
            'minLatE6': field['minLatE6'],
            'maxLngE6': field['maxLngE6'],
            'minLngE6': field['minLngE6'],
        }
        self.point = {
            'latE6': (field['maxLatE6'] + field['minLatE6']) >> 1,
            'lngE6': (field['maxLngE6'] + field['minLngE6']) >> 1,
        }
        self.version = self.get_version()

    def get_version(self):
        """refresh api version for request"""
        request = requests.get('https://www.ingress.com/intel', headers=self.headers)
        return re.findall(r'gen_dashboard_(\w*)\.js', request.text)[0]

    def check_account(self):
        if self.account['expires'] >= time.time(): # TODO fix this
            raise AccountExpiresException(self.account['_id'])

    def fetch(self, url, payload):
        """raw request with auto-retry and connection check function"""
        payload['v'] = self.version
        self.check_account()
        try:
            request = requests.post(url, data=json.dumps(payload), headers=self.headers)
            return request.json()['result']
        except:
            raise AccountBannedException(self.account['_id'])

    def fetch_msg(self, mints=-1, maxts=-1, reverse=False, tab='all'):
        """fetch message from ingress COMM, tab can be 'all', 'faction', 'alerts'"""
        url = 'https://www.ingress.com/r/getPlexts'
        payload = {
            'maxLatE6': self.field['maxLatE6'],
            'maxLngE6': self.field['maxLngE6'],
            'maxTimestampMs': maxts,
            'minLatE6': self.field['minLatE6'],
            'minLngE6': self.field['minLngE6'],
            'minTimestampMs': mints,
            'tab': tab
        }
        if reverse:
            payload['ascendingTimestampOrder'] = True
        return self.fetch(url, payload)

    def fetch_map(self, tilekeys):
        """fetch game entities from ingress map"""
        url = 'https://www.ingress.com/r/getEntities'
        payload = {
            'tileKeys': tilekeys
        }
        return self.fetch(url, payload)

    def fetch_portal(self, guid):
        """fetch portal details from ingress"""
        url = 'https://www.ingress.com/r/getPortalDetails'
        payload = {
            'guid': guid
        }
        return self.fetch(url, payload)

    def fetch_score(self):
        """fetch the global score of RESISTANCE and ENLIGHTENED"""
        url = 'https://www.ingress.com/r/getGameScore'
        payload = {}
        return self.fetch(url, payload)

    def fetch_region(self):
        """fetch the region info of RESISTANCE and ENLIGHTENED"""
        url = 'https://www.ingress.com/r/getRegionScoreDetails'
        payload = {
            'lngE6': self.point['lngE6'],
            'latE6': self.point['latE6'],
        }
        return self.fetch(url, payload)

    def fetch_artifacts(self):
        """fetch the artifacts details"""
        url = 'https://www.ingress.com/r/getArtifactPortals'
        payload = {}
        return self.fetch(url, payload)

    def send_msg(self, msg, tab='all'):
        """send a message to Ingress COMM, tab can be 'all', 'faction'"""
        url = 'https://www.ingress.com/r/sendPlext'
        payload = {
            'message': msg,
            'latE6': self.point['latE6'],
            'lngE6': self.point['lngE6'],
            'tab': tab
        }
        return self.fetch(url, payload)

    def send_invite(self, address):
        """send a recruit to an email address"""
        url = 'https://www.ingress.com/r/sendInviteEmail'
        payload = {
            'inviteeEmailAddress': address
        }
        return self.fetch(url, payload)

    def redeem_code(self, passcode):
        """redeem a passcode"""
        url = 'https://www.ingress.com/r/redeemReward'
        payload = {
            'passcode': passcode
        }
        return self.fetch(url, payload)
