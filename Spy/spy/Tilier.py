from spy.api.utils import calc_tile, get_field, get_tile_center_lng_lat, get_tile_bounds


class Tilier:
    def __init__(self, config):
        self.config = config

    def getTiles(self):
        field = get_field(self.config['base_lng'], self.config['base_lat'], 10)
        fetch_zoom = 14
        minxtile, maxytile = calc_tile(field['minLngE6'] / 1E6, field['minLatE6'] / 1E6, fetch_zoom)
        maxxtile, minytile = calc_tile(field['maxLngE6'] / 1E6, field['maxLatE6'] / 1E6, fetch_zoom)
        tiles = []
        for xtile in range(minxtile, maxxtile + 1):
            for ytile in range(minytile, maxytile + 1):
                lng, lat = get_tile_center_lng_lat(xtile, ytile, fetch_zoom)
                tiles.append({
                    'tile': '13_{}_{}_2_8_100'.format(xtile, ytile),
                    'centerLng': lng,
                    'centerLat': lat,
                    'bounds': get_tile_bounds(xtile, ytile, fetch_zoom)
                })
        return tiles
