import numpy as np

import cadaster
import weather
from photovoltaic_module import PhotovoltaicModel
import loadprofile


def get_pv_maximum_output(
        irradiance: list,                       # list of hourly irradiance on tilted surface, list per surface
        weather_profile: weather.WeatherData,
        panel: PhotovoltaicModel,
        roof_index: int
):

    daily_power = [[panel.get_mpp(
        t=weather_profile.temperature[day * 24 + hour],
        g=irradiance[day * 24 + hour],
        vw=weather_profile.wind_speed[day * 24 + hour]
    ) for hour in range(24)] for day in range(365)]

    return daily_power


class FrozenClass(object):
    __is_frozen = False

    def __setattr__(self, key, value):
        if self.__is_frozen and not hasattr(self, key):
            raise TypeError("%r is a frozen class" % self)
        object.__setattr__(self, key, value)

    def _freeze(self):
        self.__is_frozen = True


class SimulationResult(FrozenClass):
    """
    p_dc_hourly: DC output of the PV array in an hourly format in [Wh]
    p_ac_hourly: AC output of the PV array in an hourly format in [Wh]
    p_pv2load_hourly: AC power delivered to the load by the PV in an hourly format in [Wh]
    p_balance_hourly: AC power balance in an hourly format [Wh]
    p_bat2load_hourly: AC power delivered to the load by the BESS in an hourly format in [Wh]

    """
    def __init__(self):
        self.p_dc_hourly = None
        self.p_ac_hourly = None
        self.p_pv2load_hourly = None
        self.p_balance_hourly = None
        self.p_bat2load_hourly = None
        self.bat_soc_hourly = None

        self.energy_dc_annually = None
        self.energy_ac_annually = None

        self.energy_pv2load_annually = None
        self.energy_pv2bess_annually = None
        self.energy_pv2grid_annually = None

        self.energy_pv_bess2load_annually = None

        self.energy_bess2load_annually = None
        self.energy_grid2load_annually = None

        self.energy_bess_loss_annually = None

        self.net_annual_bill_annually = None

        self.lcoe = None
        self.lcoe_pv = None
        self.lcoe_bess = None
        self.lifetime_bess = None

        self.c_nom_cost = None

        self.self_sufficiency = None
        self.self_consumption = None

        self.cost_annual_bess = None
        self.cost_annual_pv = None

        self.grid_compensation_total = None

        self.equity = None

        self.annual_costs_with_system = None
        self.annual_savings = None
        self.return_on_investment = None

        self._freeze()


class SimulationParams:
    def __init__(
            self,
            cost_bat_kwh=350,
            bat_eff=0.92,
            cost_kwh_grid=0.3104,
            pv_lifetime=25,
            maintenance=0.015,
            inflation_rate=0,
            pv_discount_rate=4e-2,
            battery_discount_rate=7.7e-2,
            inverter_eff=0.97,
            c_feedin0_kwh=0.1,
            i_feedin_monthly=1.4746e-2,
            annual_follow_on_costs=0,
            additional_costs=0,
            min_soc=0.10,
            max_soc=0.95,
    ):
        self.cost_bat_kwh=cost_bat_kwh
        self.bat_eff=bat_eff
        self.cost_kwh_grid=cost_kwh_grid
        self.pv_lifetime=pv_lifetime
        self.maintenance=maintenance
        self.inflation_rate=inflation_rate
        self.pv_discount_rate=pv_discount_rate
        self.battery_discount_rate=battery_discount_rate
        self.inverter_eff=inverter_eff
        self.c_feedin0_kwh=c_feedin0_kwh
        self.i_feedin_monthly=i_feedin_monthly
        self.annual_follow_on_costs=annual_follow_on_costs
        self.additional_costs=additional_costs
        self.min_soc=min_soc
        self.max_soc=max_soc
        self.diffuse_model=diffuse_model


class Simulation:
    def __init__(
            self,
            address: str,
            panel: PhotovoltaicModel,
            load_profile: dict,
            params: SimulationParams,
            minute_modifer=+0.5,
    ):
        self.result = SimulationResult()
        self.address = address
        self.zip_code = address.split(',')[1].strip().split(' ')[0]
        self.panel = panel
        self.params = params

        building = cadaster.by_address(address)

        self.roof_df = cadaster.get_surfaces_info(
            building=building,
            panel_width=panel.width,
            panel_height=panel.height,
            min_inclination=15,
            max_inclination=45
        )

        self.weather = weather.by_zip_code(self.zip_code, minute_modifier=minute_modifer)

        # get incident radiation on each surface
        annual_irradiance = []
        incident_irradiance = []

        for index, row in self.roof_df.iterrows():
            irradiance = weather.get_incident_radiation(
                self.weather,
                inclination=row['slope'],
                azimuth=row['orientation'],
                albedo=0.2,
                diffuse_model=params.diffuse_model,
                roof_index=index
            )

            annual_irradiance.append(sum(irradiance))
            incident_irradiance.append(irradiance)

        self.roof_df = self.roof_df.assign(annual_irradiance=annual_irradiance)

        self.ids_by_annual_irr = list(range(self.roof_df.shape[0]))
        self.ids_by_annual_irr.sort(
            key=lambda x: self.roof_df.loc[x]['annual_irradiance'], reverse=True
        )
        self.max_panels_per_surface = self.roof_df['max_num_panels'].tolist()

        # maximum power by surface for one panel
        self.p_maxs = np.array([
            get_pv_maximum_output(
                irradiance=incident_irradiance[i],
                weather_profile=self.weather,
                panel=panel,
                roof_index=i
            )
            for i in range(len(incident_irradiance))
        ])

        self.p_load = np.array([
            loadprofile.by_day_of_year(
                day_num=d,
                **load_profile
            )
            for d in range(365)
        ])



