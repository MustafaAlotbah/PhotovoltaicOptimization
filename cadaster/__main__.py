# this file is to access pre-processed ArcGIS files from
# https://www.opengeodata.nrw.de/produkte/umwelt_klima/klima/solarkataster/photovoltaik/
# after having been processed by the preprocessor


import zipfile
import os
from .utils import *
import json
from utils import request_location

import geopandas
from .geometry import f_fit, smooth_shape_n


COLS = ['suitability', 'area', 'net_area', 'slope', 'orientation']

CADASTER_PATH = '../data/cadaster'


def get_building(lon: float, lat: float, gemeinde: str) -> dict:
    gemeinde = gemeinde.lower()
    _CADASTER_PATH = os.path.join(
        os.path.split(
            os.path.split(os.path.abspath(__file__))[0]
        )[0],
        CADASTER_PATH[3:]
    )

    zip_path = os.path.join(_CADASTER_PATH, gemeinde + '.zip')

    if not os.path.exists(zip_path):
        raise BuildingNotFoundException(f"No entry for the city {gemeinde} is available at the moment!")


    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        entries = zip_ref.namelist()[1:]
        result = None

        for entry in entries:

            infos = entry[len(f"{gemeinde}/")+4:-len('.json')]
            lats = [float(lon) for lon in infos.split('_')]

            _lat = round(lat, 5)  # precision of the entries

            if lats[0] <= _lat <= lats[1]:
                # check this batch
                zip_ref.extract(entry, './temp/')
                with open('./temp/' + entry, 'r', encoding='utf-8') as batch_file:
                    buildings = json.load(batch_file)

                for building in buildings:
                    lat1, lon1, lat2, lon2 = building['bounds']
                    if min(lon1, lon2) <= lon <= max(lon1, lon2):
                        if min(lat1, lat2) <= lat <= max(lat1, lat2):
                            result = building
                            break

                os.remove('./temp/' + entry)
                os.rmdir("./temp/" + gemeinde)
                os.rmdir("./temp/")

                if result:
                    break

    if building is None:
        raise BuildingNotFoundException(f"Location's coordinates ({lon}, {lat}) is not included in the city's database!")

    return result


def get_surfaces_info(building, panel_width, panel_height, min_inclination=15, max_inclination=45):
    ids = []
    geos = []
    slopes = []
    orientations = []
    suitability = []
    area = []
    net_area = []
    max_dist = []
    panel_positions = []
    max_num_panels = []
    num_panels_assigned = []

    for surface_i in range(len(building['surfaces'])):
        ids.append(surface_i)
        slopes.append(building['surfaces'][surface_i]['props']['neigung'])
        orientations.append(building['surfaces'][surface_i]['props']['richtung'])
        suitability.append(building['surfaces'][surface_i]['props']['eigngpv'])
        area.append(building['surfaces'][surface_i]['props']['modarea'])
        net_area.append(building['surfaces'][surface_i]['props']['modanetto'])
        max_dist.append(building['surfaces'][surface_i]['props']['euk_max'])
        surfaces = building['surfaces'][surface_i]['geo']
        geos.append(
            MultiPolygon([Polygon(
                # surfaces[i]
               smooth_shape_n(surfaces[i], n=3)
            ) # .simplify(0.5)
                          for i in range(len(surfaces))])
        )

        if min_inclination <= slopes[-1] <= max_inclination:
            poss = f_fit(surfaces[0], orientations[-1], panel_width, panel_height, surfaces=surfaces[1:])
        else:
            poss = []

        panel_positions.append(poss)
        max_num_panels.append(len(poss))
        num_panels_assigned.append(0)


    d = {
        'id': ids,
        'suitability': suitability,
        'area': area,
        'net_area': net_area,
        'slope': slopes,
        'orientation': orientations,
        'max_num_panels': max_num_panels,
        'num_panels_assigned': num_panels_assigned,
        'panels_positions': panel_positions,
        'max_dist': max_dist,
        'color': [(x / 180, 0, 0) for x in slopes],
        'geometry': geos,
    }

    gdf = geopandas.GeoDataFrame(d, crs=25832)

    return gdf  # .to_crs(4326)


def by_address(addr: str) -> geopandas.GeoDataFrame:
    osm_b = request_location(addr, building=True)
    gemeinde = None
    lon, lat = None, None

    if osm_b:
        lon = float(osm_b['lon'])
        lat = float(osm_b['lat'])
        addr = osm_b['address']
        city_type = 'city'

        if 'town' in addr.keys():
            city_type = 'town'

        if city_type in addr.keys():
            gemeinde = addr[city_type]

    if gemeinde and lon and lat:
        building = get_building(lon, lat, gemeinde)
        return building

    raise BuildingNotFoundException("")











