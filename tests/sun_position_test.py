import sun_position
import weather
import matplotlib.pyplot as plt



# this is a simple demonstration for the usage of the sun_position module on its own
if __name__ == "__main__":

    weather_profile = weather.by_zip_code('52062')

    sunpos = [
        sun_position.by_hour_of_year(h - 0.5,
                                     weather_profile.longitude, weather_profile.latitude, timezone=1,
                                     year=2022, site_elev=0,
                                     temp=weather_profile.temperature[h], pressure=weather_profile.pressure[h]
                                     )
        for h in range(8760)
    ]

    altitude, azimuth, sun_rise, sun_set = list(map(list, zip(*sunpos)))

    fig = plt.figure(figsize=(12, 12))

    ax_alt = plt.subplot(2, 2, 1)
    ax_azi = plt.subplot(2, 2, 2)
    ax_day = plt.subplot(2, 1, 2)

    ax_alt.plot(altitude)
    ax_azi.plot(azimuth)
    ax_day.plot(sun_rise, label="Sun rise")
    ax_day.plot(sun_set, label="Sun rise")
    ax_day.legend()

    ax_alt.set_title("Sun's altitude")
    ax_azi.set_title("Sun's azimuth")
    ax_day.set_title("Sunset and sunrise hours")

    fig.suptitle("Sun position by SPA")

    plt.show()