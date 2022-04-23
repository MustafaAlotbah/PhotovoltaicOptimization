import matplotlib.pyplot as plt
import photovoltaic_module
import weather, sun_position



if __name__ == "__main__":

    zip_code = '52074'
    panel_inclination = 21
    panel_azimuth = 205
    year = 2008
    site_elev = 0
    timezone = 1
    minute_modifier = +0.5

    # data
    weather_profile = weather.by_zip_code(zip_code)

    sun_pos = [sun_position.by_hour_of_year(
        hour_of_year=i + minute_modifier,
        lon=weather_profile.longitude,
        lat=weather_profile.latitude,
        timezone=timezone,
        year=year,
        site_elev=site_elev,
        pressure=weather_profile.pressure[i],
        temp=weather_profile.temperature[i]
    )
        for i in range(8760)]

    incident_radiation = weather.get_incident_radiation(
        weather_profile=weather_profile,
        inclination=panel_inclination,
        azimuth=panel_azimuth,
        roof_index=0,
        albedo=0.2
    )

    pv_panel = photovoltaic_module.SimpleEfficiencyModel(dict(
        mu_mpp=-0.351, mpp=300, width=1, height=1.63, cost=420
    ))

    p_dc = [pv_panel.get_mpp(
        t=weather_profile.temperature[i],
        g=incident_radiation[i],
        vw=weather_profile.wind_speed[i]
    ) for i in range(8760)]

    print(sum(p_dc)/1000)
    plt.grid()
    plt.plot(p_dc)
    plt.show()



