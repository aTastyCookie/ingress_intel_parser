class Portal:
    def __init__(self):
        self.core_portal_data_length = 4
        self.summary_portal_data_length = 14
        self.detailed_portal_data_length = self.summary_portal_data_length + 4

    def parseMod(self, list):
        if list is None:
            return {}
        return {
            'owner': list[0],
            'name': list[1],
            'rarity': list[2],
            'stats': list[3],
        }

    def parseResonator(self, list):
        if list is None:
            return {}
        return {
            'owner': list[0],
            'level': list[1],
            'energy': list[2],
        }

    def parseArtifactBrief(self, list):
        def decode(list):
            result = {}
            for i, arr in iter(list):
                result[arr[0]] = arr[:1]
            return result

        return {
            'fragment': decode(list[0]),
            'target': decode(list[1]),
        }

    def parseArtifactDetail(self, list):
        if (len(list) == 3 and list[0] == "" and list[1] == "" and len(list[2]) == 0):
            return None
        return {
            'type': list[0],
            'displayName': list[1],
            'fragments': list[2],
        }

    def corePortalData(self, list):
        return {
            'team': list[1],
            'latE6': list[2] / 1E6,
            'lngE6': list[3] / 1E6,
            'history': [],
        }

    def summaryPortalData(self, list):
        data = {
            'level': list[4],
            'health': list[5],
            'resCount': list[6],
            'image': list[7],
            'title': list[8],
            'ornaments': list[9],
            'mission': list[10],
            'mission50plus': list[11],
            'capturedTimestamp': list[13]
        }
        if list[12] is not None:
            data['artifactBrief'] = self.parseArtifactBrief(list[12])
        return data

    def portalSummary(self, dict):
        if dict[0] != 'p':
            raise Exception('Error: EntityDecoder.portalSummary - not a portal')
        if len(dict) == self.core_portal_data_length:
            return self.corePortalData(dict)
        if len(dict) != self.summary_portal_data_length and len(dict) != self.detailed_portal_data_length:
            print('Portal summary length changed - portal details likely broken!')
        data = self.corePortalData(dict)
        data.update(self.summaryPortalData(dict))
        return data

    def portalDetail(self, dict):
        if dict[0] != 'p':
            raise Exception('Error: EntityDecoder.portalDetail - not a portal')
        if len(dict) != self.detailed_portal_data_length:
            print('Portal summary length changed - portal details likely broken!')
        data = self.corePortalData(dict)
        data.update(self.summaryPortalData(dict))
        data.update({
            'mods': [self.parseMod(x) for x in dict[self.summary_portal_data_length] ],
            'resonators': [self.parseResonator(x) for x in dict[self.summary_portal_data_length + 1] ],
            'owner': dict[self.summary_portal_data_length + 2],
            'artifactDetail': self.parseArtifactDetail(dict[self.summary_portal_data_length + 3]),
        })
        return data
