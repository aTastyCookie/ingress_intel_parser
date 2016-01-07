from datetime import datetime, timedelta


class Message(object):
    @staticmethod
    def parse(dict):
        seconds = dict[1] / 1000
        return {
            'guid': dict[0],
            'time': seconds,
            'text': dict[2]['plext']['text'],
            'type': dict[2]['plext']['plextType'],
            'team': dict[2]['plext']['team'],
            'markup': dict[2]['plext']['markup'],
        }
