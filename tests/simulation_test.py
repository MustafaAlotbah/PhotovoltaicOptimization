from simulation import Simulation, simulate, SimulationParams
from photovoltaic_module import SimpleEfficiencyModel, load_simple_models
from loadprofile import ProfileType, ResidentialBuildingType, ResidentialRating
import pandas as pd

pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

COLS = ['id', 'suitability', 'slope', 'orientation', 'max_num_panels', 'num_panels_assigned', 'annual_irradiance']


if __name__ == "__main__":

    # Inputs

    address = "Eupenerstr 270, 52076 Aachen"

    panel_models = load_simple_models(file_path='../data/simple_models.json')

    if len(panel_models) <= 0:
        print("Panels data-set is empty!")

    panel = SimpleEfficiencyModel(panel_models[0])

    load_profile = dict(
        profile=ProfileType.Residential,
        number_of_residents=3,
        building_type=ResidentialBuildingType.House,
        is_warm_water_electric=False,
        rating=ResidentialRating.D,
    )

    params = SimulationParams(
        bat_eff=0.92,
        pv_lifetime=25,
        maintenance=0.01,

        inflation_rate=0.025,
        pv_discount_rate=0.04,
        battery_discount_rate=0.03,
        inverter_eff=0.97,

        cost_bat_kwh=850,
        cost_kwh_grid=0.3983,
        c_feedin0_kwh=0.0167,
        i_feedin_monthly=1.4746e-2,
        annual_follow_on_costs=0,
        additional_costs=200,

        min_soc=0.10,
        max_soc=0.95
    )

    # Simulations

    sim = Simulation(address=address, panel=panel, load_profile=load_profile, params=params, minute_modifer=-0.5)

    print("Annual load", sim.p_load.sum()/1000)

    lcoe = simulate(
        n_modules=6,
        c_nom=1000,
        simulation=sim,
    )
    print(f"LCOE: {lcoe*100:.2f} ct/kWh")
    print("-"*20)
    # assertions

    assert int(sim.result.energy_pv2bess_annually*1000 +
               sim.result.energy_pv2grid_annually*1000 +
               sim.result.energy_pv2load_annually*1000) == int(sim.result.energy_ac_annually * 1000)

    assert int(sim.result.energy_grid2load_annually*1000 +
               sim.result.energy_bess2load_annually*1000 +
               sim.result.energy_pv2load_annually*1000) == int(sim.p_load.sum())

    # print results

    width = len(max(vars(sim.result), key=len)) + 2
    for var in vars(sim.result):
        if not var.endswith('hourly') and not var.startswith('_'):
            unit = ""
            multiplier = 1
            if var.startswith("energy_") and var.endswith("_annually"):
                unit = "kWh"
            if var.startswith("lcoe"):
                unit = "ct/kWh"
                multiplier = 100
            if var.startswith("life"):
                unit = "years"
            if var.startswith("self"):
                unit = "%"
                multiplier = 100
            if any([word in var for word in ["cost", "bill", "compensation", "equity"]]):
                unit = "EUR"

            value = f"{vars(sim.result)[var] * multiplier:.2f}"
            print(var + " " * (width-len(var)) + value + " " * (8 - len(value)) + unit)

    print(sim.roof_df[COLS])