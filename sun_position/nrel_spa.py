import ctypes
import os


__day_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def get_month(n):
    for m in range(len(__day_in_month)):
        if __day_in_month[m] -n > 0:
            return m
        n -= __day_in_month[m]


def get_day_month(day_year):
    day_year += 1
    elapsed_days = 1
    month = get_month(day_year-1)
    for i in range(month):
        elapsed_days += __day_in_month[i]
    return day_year - elapsed_days + 1


def get_hourly_sunpos_spa(year, minute,
                          lat, lon, timezone,
                          site_elev, pressure, temp, tilt, azm_rotation):

    path = "/".join(os.path.abspath(__file__).split("\\")[:-1] + ['nrel_spa.dll'])
    c_lib = ctypes.CDLL(path)

    year = ctypes.c_int32(year)
    minute = ctypes.c_double(minute)
    lat = ctypes.c_double(lat)
    lon = ctypes.c_double(lon)
    timezone = ctypes.c_double(timezone)
    site_elev = ctypes.c_double(site_elev)
    pressure = ctypes.c_double(pressure)
    temp = ctypes.c_double(temp)
    tilt = ctypes.c_double(tilt)
    azm_rotation = ctypes.c_double(azm_rotation)

    sun_alt = (ctypes.c_double * 8760)(*[0]*8760)
    sun_azi = (ctypes.c_double * 8760)(*[0]*8760)
    sun_rise = (ctypes.c_double * 8760)(*[0]*8760)
    sun_set = (ctypes.c_double * 8760)(*[0]*8760)

    getattr(c_lib, "get_sam_sunpos_array")(
        year, minute, lat, lon, timezone, site_elev, pressure, temp, tilt, azm_rotation,
        ctypes.byref(sun_alt), ctypes.byref(sun_azi), ctypes.byref(sun_rise), ctypes.byref(sun_set)
    )

    return list(sun_alt), list(sun_azi), list(sun_rise), list(sun_set)


# Windows or linux
if os.environ.get('OS','').lower().startswith('win'):
    path = "/".join(os.path.abspath(__file__).split("\\")[:-1] + ['shared_library/nrel_spa.dll'])
else:
    path = "/".join(os.path.abspath(__file__).split("/")[:-1] + ['shared_library/nrel_spa.so'])

c_lib = ctypes.CDLL(path)

def get_sunpos_spa(year, month, day, hour, minute, second,
                   lat, lon, timezone,
                   site_elev, pressure, temp, inclination, azm_rotation):


    year = ctypes.c_int32(year)
    month = ctypes.c_int32(month)
    day = ctypes.c_int32(day)
    hour = ctypes.c_int32(hour)
    minute = ctypes.c_double(minute)
    second = ctypes.c_double(second)
    lat = ctypes.c_double(lat)
    lon = ctypes.c_double(lon)
    timezone = ctypes.c_double(timezone)
    site_elev = ctypes.c_double(site_elev)
    pressure = ctypes.c_double(pressure)
    temp = ctypes.c_double(temp)
    inclination = ctypes.c_double(inclination)
    azm_rotation = ctypes.c_double(azm_rotation)

    sun_alt = ctypes.c_double(0)
    sun_azi = ctypes.c_double(0)
    sun_rise = ctypes.c_double(0)
    sun_set = ctypes.c_double(0)

    getattr(c_lib, "get_sam_sunpos")(
        year, month, day, hour, minute, second, lat, lon, timezone, site_elev, pressure, temp, inclination, azm_rotation,
        ctypes.byref(sun_alt), ctypes.byref(sun_azi), ctypes.byref(sun_rise), ctypes.byref(sun_set)
    )

    return sun_alt.value, sun_azi.value, sun_rise.value, sun_set.value


# get sun_position position by hour of year (float)
def by_hour_of_year(hour_of_year, lon, lat, timezone, site_elev, pressure=1023.25, temp=15, inclination=0, azm_rotation=0, year=2008):
    hour_of_year = hour_of_year % 8760
    month = get_month(int(hour_of_year) // 24) + 1
    day_of_month = get_day_month(int(hour_of_year)//24)
    hour_of_day = int(hour_of_year % 24)
    minute = (hour_of_year % 1) * 60

    return get_sunpos_spa(year, month, day_of_month, hour_of_day, minute,
                          second=0,
                          lat=lat, lon=lon,
                          timezone=timezone,
                          site_elev=site_elev,
                          pressure=pressure,
                          temp=temp,
                          inclination=inclination,
                          azm_rotation=azm_rotation
                          )








