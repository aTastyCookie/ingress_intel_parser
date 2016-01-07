import math
import mercantile

tilecounts = [1, 1, 1, 40, 40, 80, 80, 320, 1000, 2000, 2000, 4000, 8000, 16000, 16000, 32000, 32000]


def calc_tile(lng, lat, zoom):
    lat = math.radians(lat)
    n = tilecounts[zoom]
    xtile = int(math.floor((lng + 180.0) / 360.0 * n))
    ytile = int(math.floor((1.0 - math.log(math.tan(lat) + (1.0 / math.cos(lat))) / math.pi) / 2.0 * n))
    return xtile, ytile


def ul(xtile, ytile, zoom):
    """Returns the upper left (lon, lat) of a tile"""
    n = tilecounts[zoom]
    lng_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lng_deg, lat_deg


def get_tile_bounds(xtile, ytile, zoom):
    a = ul(xtile, ytile, zoom)
    b = ul(xtile + 1, ytile + 1, zoom)
    return {
        'west': a[0],
        'south': b[1],
        'east': b[0],
        'north': a[1]
    }


def get_tile_center_lng_lat(xtile, ytile, zoom):
    bounds = get_tile_bounds(xtile, ytile, zoom)
    return (bounds['west'] + bounds['east']) / 2, (bounds['north'] + bounds['south']) / 2


def get_field(centerLng, centerLat, zoom):
    xtile, ytile = calc_tile(centerLng, centerLat, zoom)
    bounds = get_tile_bounds(xtile, ytile, zoom)
    return {
        'maxLngE6': int(bounds['east'] * 1E6),
        'maxLatE6': int(bounds['north'] * 1E6),
        'minLngE6': int(bounds['west'] * 1E6),
        'minLatE6': int(bounds['south'] * 1E6)
    }
