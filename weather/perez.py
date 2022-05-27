"""
Perez model
Source: https://www.nrel.gov/docs/fy15osti/64102.pdf (p. 24)
"""

from math import sin, cos, pi, acos
from .weather_profile import WeatherData

def deg2rad(a):
    return a * pi / 180


def rad2deg(a):
    return a * 180 / pi


# Perez model constants
f11 = [-0.0083117,  0.1299457,  0.3296958,  0.5682053,  0.873028,   1.1326077,  1.0601591,  0.6777470  ]
f12 = [ 0.5877285,  0.6825954,  0.4868735,  0.1874525, -0.3920403, -1.2367284, -1.5999137, -0.3272588  ]
f13 = [-0.0620636, -0.1513752, -0.2210958, -0.2951290, -0.3616149, -0.4118494, -0.3589221, -0.2504286  ]
f21 = [-0.0596012, -0.0189325,  0.0554140,  0.1088631,  0.2255647,  0.2877813,  0.2642124,  0.1561313  ]
f22 = [ 0.0721249,  0.065965,  -0.0639588, -0.1519229, -0.4620442, -0.8230357, -1.127234,  -1.3765031  ]
f23 = [-0.0220216, -0.0288748, -0.0260542, -0.0139754,  0.0012448,  0.0558651,  0.1310694,  0.2506212  ]

k = 5.534e-6  # for angles in degrees


def sky_clearness_to_eta_bin(sky_clearness):
    if sky_clearness <= 1.065:
        return 1
    if sky_clearness <= 1.230:
        return 2
    if sky_clearness <= 1.500:
        return 3
    if sky_clearness <= 1.950:
        return 4
    if sky_clearness <= 2.800:
        return 5
    if sky_clearness <= 4.500:
        return 6
    if sky_clearness <= 6.200:
        return 7
    return 8


def get_f(f: list, sky_clearness: float):
    return f[sky_clearness_to_eta_bin(sky_clearness)-1]


# absolute optical air mass with angles in degrees (AM0)
def airmass(angle_of_incidence_rad: float, sun_altitude_deg):
    return (cos(deg2rad(90 - sun_altitude_deg)) + 0.15 * (sun_altitude_deg + 3.9)**(-1.253))**-1


def delta(dhi: float, airmass: float) -> float:
    return dhi * airmass / 1367  # extraterrestrial irradiance


def sky_clearness(dhi: float, dni: float, sun_alt_deg: float) -> float:
    _a = (dhi + dni)/dhi
    _k_sun_azimuth_3 = k * (90 - sun_alt_deg)**3
    return (_a + _k_sun_azimuth_3)/(1 + _k_sun_azimuth_3)


def f1(_delta: float, sun_alt_rad: float, sky_clearness: float):
    _f11 = get_f(f11, sky_clearness)
    _f12 = get_f(f12, sky_clearness)
    _f13 = get_f(f13, sky_clearness)
    return max(0, _f11 + _f12 * _delta + (pi/2 - sun_alt_rad) * _f13)


def f2(_delta: float, sun_alt_rad: float, sky_clearness: float):
    _f21 = get_f(f21, sky_clearness)
    _f22 = get_f(f22, sky_clearness)
    _f23 = get_f(f23, sky_clearness)
    return _f21 + _f22 * _delta + (pi/2 - sun_alt_rad) * _f23


def a(angle_of_incidence):
    return max(0, cos(angle_of_incidence))


def b(angle_of_incidence):
    return max(cos(deg2rad(85)), cos(angle_of_incidence))


def perez_diffusion(inclination: float, azimuth: float, weather_profile: WeatherData) -> list:

    ls = []
    absolute_airmass = []



    for i in range(8760):

        if azimuth == 205 and i == 40:
            print("hi")

        sun_alt_deg = weather_profile.sun_altitude[i]
        sun_azi_deg = weather_profile.sun_azimuth[i]

        dni = weather_profile.direct_horizontal_irradiance[i] / sin(deg2rad(sun_alt_deg))
        dhi = weather_profile.diffuse_horizontal_irradiance[i]

        _di = 0
        _dc = 0
        _dh = 0
        _airmass = 0

        if sun_alt_deg > -0.25:
            _di = dhi * (1 + cos(deg2rad(inclination))) / 2

        if sun_alt_deg > 2.5:
            theta_incidence = cos(deg2rad(sun_alt_deg)) * sin(deg2rad(inclination)) * cos(
                deg2rad(azimuth - sun_azi_deg)) \
                              + sin(deg2rad(sun_alt_deg)) * cos(deg2rad(inclination))
            theta_incidence = acos(theta_incidence)

            _sky_clearness = sky_clearness(dhi=dhi, dni=dni, sun_alt_deg=sun_alt_deg)
            _airmass = airmass(theta_incidence, sun_alt_deg)
            _delta = delta(dhi=dhi, airmass=_airmass)

            _f1 = f1(_delta=_delta, sun_alt_rad=deg2rad(sun_alt_deg), sky_clearness=_sky_clearness)
            _f2 = f2(_delta=_delta, sun_alt_rad=deg2rad(sun_alt_deg), sky_clearness=_sky_clearness)

            _a = a(theta_incidence)
            _b = b(deg2rad(90 - sun_alt_deg))

            _di = dhi * (1 - _f1) * (1 + cos(deg2rad(inclination))) / 2
            _dc = dhi * _f1 * _a / _b
            _dh = dhi * _f2 * sin(deg2rad(inclination))



        ls.append(_di + _dc + _dh)
        absolute_airmass.append(_airmass)


    return ls






















