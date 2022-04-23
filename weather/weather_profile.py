
import zipfile
import os
import sun_position

#
#
DWD_DATASET_PATH = 'data/dwd_zips.zip'
SUB_FOLDER = 'dwd_zips/'


def set_dataset_path(path):
    global DWD_DATASET_PATH
    DWD_DATASET_PATH = path


def get_dataset_path():
    return DWD_DATASET_PATH


'''
Data as given in the DWD dataset:

RW Rechtswert                                                    [m]       {3670500;3671500..4389500}
HW Hochwert                                                      [m]       {2242500;2243500..3179500}
MM Monat                                                                   {1..12}
DD Tag                                                                     {1..28,30,31}
HH Stunde (MEZ)                                                            {1..24}
t  Lufttemperatur in 2m Hoehe ueber Grund                        [GradC]
p  Luftdruck in Standorthoehe                                    [hPa]
WR Windrichtung in 10 m Hoehe ueber Grund                        [Grad]    {0..360;999}
WG Windgeschwindigkeit in 10 m Hoehe ueber Grund                 [m/s]
N  Bedeckungsgrad                                                [Achtel]  {0..8;9}
x  Wasserdampfgehalt, Mischungsverhaeltnis                       [g/kg]
RF Relative Feuchte in 2 m Hoehe ueber Grund                     [Prozent] {1..100}
B  Direkte Sonnenbestrahlungsstaerke (horiz. Ebene)              [W/m^2]   abwaerts gerichtet: positiv
D  Diffuse Sonnenbetrahlungsstaerke (horiz. Ebene)               [W/m^2]   abwaerts gerichtet: positiv
A  Bestrahlungsstaerke d. atm. Waermestrahlung (horiz. Ebene)    [W/m^2]   abwaerts gerichtet: positiv
E  Bestrahlungsstaerke d. terr. Waermestrahlung                  [W/m^2]   aufwaerts gerichtet: negativ
IL Qualitaetsbit bezueglich der Auswahlkriterien                           {0;1;2;3;4}
'''


# wrapper class for weather data
class WeatherData:
    def __init__(self, data: dict):
        self.zip_code = data['zip_code']
        self.longitude = data['lon']
        self.latitude = data['lat']
        self.city_name = data['city']

        self.location = data['data']['RW'][0], data['data']['HW'][0]       # Rechtswert, Hochwert
        self.temperature = data['data']['t']
        self.pressure = data['data']['p']
        self.wind_direction = data['data']['WR']
        self.wind_speed = data['data']['WG']
        self.sky_clearness = data['data']['N']
        self.mass_mixing_ratio = data['data']['x']      # absolute humidity
        self.relative_humidity = data['data']['RF']
        self.direct_horizontal_irradiance = data['data']['B']
        self.diffuse_horizontal_irradiance = data['data']['D']

        self.sun_altitude = None
        self.sun_azimuth = None
        self.sunrise = None
        self.sunset = None

        self.length = len(self.temperature)


class RegionDoesNotExist(Exception):
    pass


def __read__lines(path):
    lines = []
    with open(path, newline='') as file:
        _lines = file.readlines()
        for line in _lines:
            lines.append(line.strip()
                         .replace('  ', ' ')
                         .replace('  ', ' ')
                         )
    return lines


def __get_processed_entry(lines):
    start_line = 34
    _ls = []
    for i in range(8760):
        curr = lines[start_line + i].split(' ')
        _ls.append(curr)
    # transpose
    res = list(map(list, zip(*_ls)))
    return {
        'RW': [int(i) for i in res[0]],
        'HW': [int(i) for i in res[1]],
        'MM': [int(i) for i in res[2]],
        'DD': [int(i) for i in res[3]],
        'HH': [int(i) for i in res[4]],
        't':  [float(i) for i in res[5]],
        'p':  [int(i) for i in res[6]],
        'WR': [int(i) for i in res[7]],
        'WG': [float(i) for i in res[8]],
        'N':  [int(i) for i in res[9]],
        'x':  [float(i) for i in res[10]],
        'RF': [int(i) for i in res[11]],
        'B':  [float(i) for i in res[12]],
        'D':  [float(i) for i in res[13]],
        'A':  [float(i) for i in res[14]],
        'E':  [float(i) for i in res[15]],
        'IL': [int(i) for i in res[16]],
    }


# get weather profile from DWD without sun_position position
def __by_zip_code(zip_code: str) -> WeatherData:
    path = os.path.join(
        os.path.split(
            os.path.split(os.path.abspath(__file__))[0]
        )[0],
        DWD_DATASET_PATH
    )

    with zipfile.ZipFile(path, 'r') as zip_ref:
        entries = zip_ref.namelist()[1:]
        for entry in entries:
            infos = entry[len(SUB_FOLDER):-len('.txt')].split('_')
            entry_zip = infos[0]
            if entry_zip == zip_code:
                # extract file
                zip_ref.extract(entry, './temp/')

                lines = __read__lines('./temp/'+entry)

                data = __get_processed_entry(lines)

                os.remove('./temp/'+entry)
                os.rmdir("./temp/"+SUB_FOLDER.split("/")[0])
                os.rmdir("./temp/")

                lon, lat = float(infos[2]), float(infos[3])
                return WeatherData({
                    'zip_code': entry_zip,
                    'city': infos[1],
                    'lon': lon,
                    'lat': lat,
                    'data': data
                })

    raise RegionDoesNotExist(f"Weather dataset does not include zip code: '{zip_code}'!")


# get weather profile with sun_position position
def by_zip_code(zip_code: str, year=2008, minute_modifier=+0.5, site_elev=0) -> WeatherData:
    weather = __by_zip_code(zip_code)

    sunpos = [
        sun_position.by_hour_of_year(h + minute_modifier,
                                     weather.longitude, weather.latitude, timezone=1,
                                     year=year, site_elev=site_elev,
                                     temp=weather.temperature[h], pressure=weather.pressure[h]
                                     )
        for h in range(8760)
    ]

    alt, azi, sunrise, sunset = list(map(list, zip(*sunpos)))

    weather.sun_altitude = alt
    weather.sun_azimuth = azi
    weather.sunrise = sunrise
    weather.sunset = sunset

    return weather
