

import geopandas
from shapely.geometry import Point, Polygon, MultiPolygon
from pyproj import CRS, Transformer

crs_europe = CRS.from_epsg(25832)
crs_wgs84 = CRS.from_epsg(4326)
coors_transform = Transformer.from_crs(crs_europe, crs_wgs84)

#
# convert from ETRS98 to WGS84 coordinates
def etrs2wgs(point):
    return coors_transform.transform(point[0], point[1])
    # d = {'col1': ['point'], 'geometry': [Point(point[0], point[1])]}
    # gdf = geopandas.GeoDataFrame(d, crs=25832)
    # gdf_new = gdf.to_crs(4326)
    # return gdf_new['geometry'][0].x, gdf_new['geometry'][0].y



def get_box(surfaces):
    # 1 is geometry
    # 0 each surface has only one polygon
    mp = MultiPolygon([Polygon(surfaces[i]['geo'][0]) for i in range(len(surfaces))])

    x1, y1 = etrs2wgs((mp.bounds[0], mp.bounds[1]))
    x2, y2 = etrs2wgs((mp.bounds[2], mp.bounds[3]))

    return x1, y1, x2, y2


class BuildingNotFoundException(Exception):
    pass







