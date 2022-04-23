
from math import cos, sin, pi, acos, floor
from .weather_profile import WeatherData


def deg2rad(a):
    return a * pi / 180


def rad2deg(a):
    return a * 180 / pi


def direct_irradiation_tilted(inclination: float, azimuth: float, weather_profile: WeatherData, radiation: list, roof_index: int):
    res = []

    # These are used for logging
    angle_inc = []
    angle_sun_alts = []
    angle_sun_azis = []

    for i in range(8760):
        sun_altitude = weather_profile.sun_altitude[i]
        gamma_s = weather_profile.sun_azimuth[i]
        sun_rise = weather_profile.sunrise[i]

        theta_incidence = cos(deg2rad(sun_altitude)) * sin(deg2rad(inclination)) * cos(deg2rad(azimuth - gamma_s)) \
                        + sin(deg2rad(sun_altitude)) * cos(deg2rad(inclination))
        theta_incidence = acos(theta_incidence)

        if sun_altitude < -0.25 or \
                not (
                        ((i % 24 + 0.5) - sun_rise) > 0 or floor(sun_rise) != floor((i % 24 + 0.5))
                ):
            theta_incidence = 0

        i_direct_tilted = cos(theta_incidence) / sin(deg2rad(sun_altitude)) * radiation[i]

        angle_sun_azis.append(gamma_s)
        angle_sun_alts.append(sun_altitude)

        i_direct_tilted = max(i_direct_tilted, 0)

        res.append(i_direct_tilted)

        angle_inc.append(theta_incidence * 180 / pi)

    # if roof_index == logger.debugging_roof_index():
    #     logger.add_column(f"sun_azi", angle_sun_azis)
    #     logger.add_column(f"sun_alt", angle_sun_alts)
    #     logger.add_column(f"angle_inc", angle_inc)

    return res


def diffuse_irradiation_tilted(inclination: float, radiation: list, weather_profile: WeatherData):
    ls = []
    for i in range(8760):
        i_diffuse_tilted = (1 + cos(deg2rad(inclination))) * radiation[i] / 2
        i_diffuse_tilted = max(i_diffuse_tilted, 0)

        if weather_profile.sun_altitude[i] < -0.25:
            i_diffuse_tilted = 0

        ls.append(i_diffuse_tilted)

    return ls


def reflected_irradiation_tilted(inclination: float, direct_radiation: list, diffuse_radiation: list, weather_profile: WeatherData, albedo=0.2):
    ls = []
    for i in range(8760):

        radiation = direct_radiation[i] + diffuse_radiation[i]
        i_reflect_tilted = (1 - cos(deg2rad(inclination))) * radiation / 2 * albedo
        i_reflect_tilted = max(i_reflect_tilted, 0)

        if weather_profile.sun_altitude[i] < -0.25:
            i_reflect_tilted = 0

        ls.append(i_reflect_tilted)

    return ls


def global_irradiation_tilted(
        inclination: float,
        azimuth: float,
        weather_profile: WeatherData,
        direct_radiation: list,
        diffuse_radiation: list,
        roof_index,
        albedo=0.2
) -> list:

    # if roof_index == logger.debugging_roof_index():
    #     logger.add_column(f"i_b_file", direct_radiation)
    #     logger.add_column(f"i_dif_file", diffuse_radiation)

    direct = direct_irradiation_tilted(inclination, azimuth, weather_profile, direct_radiation, roof_index=roof_index)
    diffuse = diffuse_irradiation_tilted(inclination, diffuse_radiation, weather_profile)
    reflect = reflected_irradiation_tilted(inclination, direct_radiation, diffuse_radiation, weather_profile, albedo=albedo)
    i_global = [direct[i] + diffuse[i] + reflect[i] for i in range(8760)]

    # if roof_index == logger.debugging_roof_index():
    #     logger.add_column(f"i_bn", direct)
    #     logger.add_column(f"i_dif", [diffuse[i] + reflect[i] for i in range(8760)])
    #     logger.add_column(f"i_dif_only", diffuse)
    #     logger.add_column(f"i_ref", reflect)
    #     logger.add_column(f"i_g", i_global)

    return i_global


def get_incident_radiation(
        weather_profile: WeatherData,
        inclination: float, azimuth,
        roof_index,
        albedo=0.2
) -> list:

    adjusted_beam = []
    sin_alt = []

    # clip direct horizontal irradiance between [0..1100]
    for h in range(8760):
        alt = weather_profile.sun_altitude[h]
        _pa = alt * pi / 180
        _si = sin(_pa)
        dni = weather_profile.direct_horizontal_irradiance[h] / _si
        dni = max(0, dni)
        dni = min(1100, dni)

        adjusted_beam.append(dni*_si)
        sin_alt.append(_si)

    return global_irradiation_tilted(
        inclination,
        azimuth,
        weather_profile,
        adjusted_beam,
        weather_profile.diffuse_horizontal_irradiance,
        albedo=albedo,
        roof_index=roof_index
    )