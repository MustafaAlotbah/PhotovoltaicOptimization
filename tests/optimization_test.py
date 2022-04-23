from simulation import Simulation, simulate, SimulationParams
from photovoltaic_module import SimpleEfficiencyModel, load_simple_models
from loadprofile import ProfileType, ResidentialBuildingType, ResidentialRating
import optimization
import time
import matplotlib.pyplot as plt


if __name__ == "__main__":

    # Inputs
    address = "Eupenerstr 270, 52076 Aachen"

    panel_models = load_simple_models(file_path='./data/simple_models.json')

    if len(panel_models) <= 0:
        print("No panels in the dataset")

    panel = SimpleEfficiencyModel(panel_models[0])

    load_profile = dict(
        profile=ProfileType.Residential,
        number_of_residents=4,
        building_type=ResidentialBuildingType.Apartment,
        is_warm_water_electric=True,
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
    print(panel.cost)
    sim = Simulation(address=address, panel=panel, load_profile=load_profile, params=params)

    print("Annual load", sim.p_load.sum()/1000)

    start_time = time.time()
    (x, y, cost), frames, iters, sims = optimization.heuristic(
        fun=simulate,
        options=dict(simulation=sim),
        n=50,
        step=(1, 600),
        stop_after=6,
    )
    tt = time.time() - start_time

    print()
    print(f"{iters}\t{sims}\t{tt:.2f}\t({x:.1f}, {y/1000:.2f})\t{cost:.2f}")

    # plotting

    fig, axs = plt.subplots(1, 2)

    axs[0].plot([i[2] for i in frames])
    axs[0].set_title("Cost per iteration")

    xs, ys, fs = list(zip(*frames))
    axs[1].plot(xs, ys)
    axs[1].set_title("Trace")
    plt.show()

    # simulate again
    simulate(
        n_modules=x,
        c_nom=y,
        simulation=sim,
    )

    # simulation assertions

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

