
import matplotlib.pyplot as plt
import weather

# this is a simple demonstration for the usage of the weather module
if __name__ == '__main__':
    weather_profile = weather.by_zip_code('52074')

    fig, axs = plt.subplots(3, 2)

    axs[0, 0].plot(weather_profile.temperature)
    axs[0, 0].set_title("Ambient temperature")

    axs[1, 0].plot(weather_profile.direct_horizontal_irradiance, label="Direct Irradiance")
    axs[1, 0].plot(weather_profile.diffuse_horizontal_irradiance, label="Diffuse Irradiance")
    axs[1, 0].set_title("Irradiance")
    axs[1, 0].legend()

    axs[0, 1].plot(weather_profile.pressure)
    axs[0, 1].set_title("Ambient pressure")

    axs[1, 1].plot(weather_profile.wind_speed)
    axs[1, 1].set_title("Wind speed")

    axs[2, 0].plot(weather_profile.sun_altitude, label="Sun altitude", alpha=0.5)
    axs[2, 0].plot(weather_profile.sun_azimuth, label="Sun azimuth", alpha=0.5)
    axs[2, 0].set_title("Sun position")
    axs[2, 0].legend()

    axs[2, 1].plot(weather_profile.sunrise, label="Sunrise")
    axs[2, 1].plot(weather_profile.sunset, label="Sunset")
    axs[2, 1].set_title("Sun position")
    axs[2, 1].legend()

    fig.suptitle(f"Weather profile for {weather_profile.city_name} ({weather_profile.zip_code})")

    for ax in fig.get_axes():
        ax.grid()

    plt.show()




