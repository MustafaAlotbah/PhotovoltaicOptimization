# this file is to pre-process raw ArcGIS files from
# https://www.opengeodata.nrw.de/produkte/umwelt_klima/klima/solarkataster/photovoltaik/
#

import zipfile
import os
import shapefile
from cadaster.utility import *
import json
import time



VERBOSE = True
duplicate_entries = ['gem_gn', 'kreis_gn', 'regbez_gn', 'planung_be']
irrelevant_entries = ['OBJECTID', 'gem_kn', 'kreis_kn', 'regbez_kn', 'geom_Lengt', 'geom_Area']


def log(msg):
    if VERBOSE:
        print(msg)

def load_raw_geoshape(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # extract
        log("extracting zip folder")
        entries = zip_ref.namelist()[1:]
        shape_entry = [entry for entry in entries if entry.endswith('.shp')][0]
        for entry in entries:
            zip_ref.extract(entry, './temp/')

        log("reading shape file")
        with shapefile.Reader(f"./temp/{shape_entry}", encoding='unicode_escape') as shape:
            shape_data = shape.shapeRecords()
            size = shape.numRecords

        # clean
        log("cleaning up zip folder")
        for entry in entries:
            os.remove('./temp/' + entry)
        os.rmdir("./temp/")


    log("sorting shape file")
    shape_data = list(shape_data)
    shape_data.sort(key=lambda x: x.__geo_interface__['properties']['geb_id'])

    # get Gemeinde name
    gem_gn = shape_data[0].__geo_interface__['properties']['gem_gn']

    return shape_data, size, gem_gn


#
def get_surface(shape_data, i) -> dict:
    building_data = shape_data[i].__geo_interface__
    return {
        'props': building_data['properties'],
        'geo_type': building_data['geometry']['type'],
        'geo': building_data['geometry']['coordinates'],
    }


def get_building_surfaces(shape_data, size, i_start):
    gen_info = {}

    surfaces = [get_surface(shape_data, i_start)]
    geb_id = surfaces[0]['props']['geb_id']
    next_i = i_start + 1

    for building in range(i_start+1, size):
        surface = get_surface(shape_data, building)

        if surface['props']['geb_id'] == geb_id:
            surfaces.append(surface)
            next_i = building + 1
        else:
            break

    for building in range(len(surfaces)):
            keys = surfaces[building]['props'].keys()
            for key in duplicate_entries:
                if key in keys:
                    gen_info[key] = surfaces[building]['props'][key]
                    surfaces[building]['props'].pop(key)

            for key in irrelevant_entries:
                if key in keys:
                    surfaces[building]['props'].pop(key)

    return surfaces, gen_info, next_i









if __name__ == "__main__":
    shape_data, size, gem_gn = load_raw_geoshape('../data/Alsdorf.zip')



    prev_geb_id = ''
    i = 0
    buildings = []
    start_time = time.time()
    while True:
        surfaces, gen_info, i = get_building_surfaces(shape_data, size, i)
        x1, y1, x2, y2 = get_box(surfaces)
        center = (x1 + x2) / 2, (y1 + y2) / 2

        building = {
            'geb_id': surfaces[0]['props']['geb_id'],
            'bounds': (x1, y1, x2, y2),
            'lon': center[0],
            'lat': center[1],
            'surfaces': surfaces,
        }

        for info in gen_info.keys():
            building[info] = gen_info[info]

        buildings.append(building)

        if i % 500 == 0:
            print(f"done {i / size * 100:.2f} %", end='')
            d_time = time.time() - start_time
            rest = (size - i) / 500 * d_time
            print(f"\t{d_time*1000:.0f} ms\t yet: {rest // 60:.0f}:{rest % 60:.0f} ")
            start_time = time.time()

        if i >= size:
            break

    #
    #

    log("sorting..")
    buildings.sort(key=lambda building: building['lon'])

    log("saving..")
    saving_path = f"../data/cadaster/{gem_gn}"
    if not os.path.exists(saving_path):
        os.makedirs(saving_path)

    step = 1000
    for i in range(0, len(buildings), step):
        lat_a = f"{buildings[i]['lon']:.5f}"
        lat_b = f"{buildings[min(i+1000, len(buildings)-1)]['lon']:.5f}"
        with open(saving_path + f"/lat_{lat_a}_{lat_b}.json", 'w', encoding='utf-8') as file:
            json.dump(buildings[i: i+step], file)

    zipf = zipfile.ZipFile(saving_path + ".zip", 'w', zipfile.ZIP_DEFLATED)

    log("zipping..")
    for root, dirs, files in os.walk(saving_path):
        for file in files:
            zipf.write(os.path.join(root, file),
                       os.path.relpath(os.path.join(root, file),
                                       os.path.join(saving_path, '..')))
            os.remove(os.path.join(root, file))


    os.rmdir(saving_path)


    print(len(buildings))
    print(size)