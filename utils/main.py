import requests
import json
import time

non_found = []


class AddressNotFoundException(Exception):
    pass


def request_location(address: str, building=False) -> dict:
    response = requests.request("GET", f"https://nominatim.openstreetmap.org/search?q={address}, Germany&limit=5&format=json&addressdetails=1")
    places = json.loads(response.text)
    match = None

    # return only buildings
    if building:
        if type(places) == list and len(places) > 0:
            for place in places:
                if place['class'] in ["building", "leisure", "shop", "amenity", "place"]:
                    match = place
                    break

    # return only places
    if type(places) == list and len(places) > 0:
        for place in places:
            if place['class'] == "place":
                match = place
                break

    if match:
        return match
    else:
        non_found.append(address)
        raise AddressNotFoundException(f"Address '{address}' either is not a building or not found!")


# wrapper function
def save_stats_and_cache(func: callable):
    def inner(*args):
        inner.all_calls += 1
        if args in inner.cache.keys():
            return inner.cache[args]
        start_time = time.time()
        res = func(*args)
        inner.durations.append(time.time() - start_time)
        inner.calls += 1
        inner.cache[args] = res
        return res

    inner.cache = {}
    inner.calls = 0
    inner.all_calls = 0
    inner.durations = []
    return inner














