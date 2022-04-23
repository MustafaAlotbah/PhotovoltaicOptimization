import os
import numpy as np
from .utils import *


def __load_h0():
    days = []
    path = os.path.dirname(os.path.abspath(__file__))
    with open(path + '/default_data/h0.txt', newline='') as file:
        lines = file.readlines()
        for line in lines:
            hours_str = line.strip().replace('\t', "").split(';')
            days.append([float(hourly_load) for hourly_load in hours_str])
    return days


#
# annual: / 1018704.4249999993 [Wh]
#
def __load_g0():
    days = []
    path = os.path.dirname(os.path.abspath(__file__))
    with open(path + '/default_data/g0.txt', newline='') as file:
        lines = file.readlines()
        for line in lines:
            hours_str = line.strip().replace('\t', "").split(';')
            days.append([float(hourly_load) for hourly_load in hours_str])
    return days


#
h0 = __load_h0()
g0 = __load_g0()

# stromspiegel 21/22
scale_stromspiegel_h0 = {
    ResidentialBuildingType.House: {
        'ohneStrom': [
            #     A     B     C     D     E     F     G
                [1300, 1600, 2000, 2500, 3200, 4100, 4100],     # one person
                [2000, 2400, 2800, 3000, 3500, 4200, 4200],     # two people
                [2500, 3000, 3400, 3700, 4200, 5000, 5000],     # three people
                [2700, 3300, 3700, 4000, 4700, 5800, 5800],
                [3200, 4000, 4500, 5000, 6000, 7500, 7500],     # more than five
        ],
        'mitStrom': [
                [1500, 1900, 2300, 2900, 3500, 5000, 5000],
                [2400, 3000, 3400, 3800, 4500, 6000, 6000],
                [3000, 3500, 4000, 4800, 5600, 7000, 7000],
                [3500, 4000, 4800, 5500, 6400, 8000, 8000],
                [4000, 5000, 6000, 6800, 8000, 10000, 10000],
        ],
    },
    ResidentialBuildingType.Apartment: {
            'ohneStrom': [
                [800, 1000, 1200, 1500, 1600, 2000, 2000],
                [1200, 1500, 1800, 2100, 2500, 3000, 3000],
                [1500, 1900, 2200, 2600, 3000, 3700, 3700],
                [1700, 2000, 2500, 2900, 3500, 4100, 4100],
                [1700, 2300, 2800, 3500, 4200, 5500, 5500],
            ],
            'mitStrom': [
                [1000, 1400, 1600, 2000, 2200, 2800, 2800],
                [1800, 2300, 2600, 3000, 3500, 4000, 4000],
                [2500, 3000, 3500, 4000, 4500, 5500, 5500],
                [2500, 3200, 4000, 4500, 5000, 6000, 6000],
                [2400, 3500, 4300, 5200, 6200, 8000, 8000],
            ],
        },
}


#
# https://www.online-energieausweis.org/verbrauchsausweis/statistiken-zum-verbrauchsausweis-gewerbe/
stromspiegel_g0_per_m2 = {
    'office': 55,
    'hotel_garni': 70,
    'retailer': 270,
    'workshop': 35,
    'production_site': 80,
    'commercial_nonfood': 90,
    'non_food_retailer': 150,
    'bakery': 500,
}

#
def get_usage(usage: str):
    usage = usage.lower()
    classes = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    if usage in classes:
        return classes.index(usage)
    else:
        return 6


def scale(ls, scalar):
    return [ls[i] * scalar for i in range(len(ls))]


# ls 2 dm array (h0, g0)
def shift_by_hour(ls, hour):
    if hour == 0:
        return ls
    shifted = np.roll(np.array(ls).flatten(), hour)
    dim = len(ls[0])
    res = [shifted[i: i+dim].tolist() for i in range(0, len(shifted), dim)]
    return res


def by_day_of_year(
        day_num,
        profile=ProfileType.Residential,
        number_of_residents=1,
        building_type=ResidentialBuildingType.House,
        is_warm_water_electric=False,
        rating=ResidentialRating.D,
        area=None,
        shift=0
):
    """
    prfile: ProfileType. [Residential, Commercial]
    rating: ResidentialRating. [A..G] | integer or float in (kWh/year)
    for Residential: parameters: num_people, building_type, warm_water_electrical, rating (class)
    for Commercial: parameters: area, building_type
    building type:
    Residential:  ResidentialBuildingType. [House, Apartment]
    Commercial:   office, hotel_garni, retailer, workshop, production_site, commercial_nonfood
    for both: usage (int, float) [kWh/year]
    """

    number_of_residents = min(number_of_residents, 6)

    # household
    if profile == ProfileType.Residential and type(rating) == str:

        rating = get_usage(rating)

        warm_water = 'ohneStrom'
        if is_warm_water_electric:
            warm_water = 'mitStrom'

        return scale(shift_by_hour(h0, shift)[day_num], scale_stromspiegel_h0[building_type][warm_water][number_of_residents - 1][rating] / 1000)

    elif profile == ProfileType.Residential and type(rating) in [float, int]:
        return scale(shift_by_hour(h0, shift)[day_num], rating / 1000)

    # Gewerbe Allgemein
    if profile == ProfileType.Commercial:
        day_of_week = day_num % 7
        if day_of_week > 1:
            day_of_week = 2
        # Winter
        if day_num > 305 or day_num < 79:
            res = g0[day_of_week]
        # Summer
        elif 135 < day_num < 257:
            res = g0[3 + day_of_week]
        # transitional season
        else:
            res = g0[6 + day_of_week]

    else:
        raise UnknownLoadProfileType(f"Unknown load profile type: {profile}!")

    if type(rating) in [float, int]:
        res = scale(res, rating / 1018.7044245)
    elif area is not None and type(rating) == str:
        res = scale(res, (stromspiegel_g0_per_m2[rating] * area)/1018.7044245)
    else:
        raise LoadProfileException(f"Area is not defined!")

    return res


#
def get_day_name(i):
    if i >= 152:
        sat_offset = 4
    else:
        sat_offset = 3
    if (i - sat_offset) % 7 == 0:
        return 'sat'
    if (i - sat_offset) % 7 == 1:
        return 'sun_position'
    return 'work'


def get_season(dayNum):
    # Winter
    if dayNum > 305 or dayNum < 79:
        return 'winter'
    # Summer
    elif 135 < dayNum < 257:
        return 'summer'
    # transition period
    else:
        return 'transitional'






