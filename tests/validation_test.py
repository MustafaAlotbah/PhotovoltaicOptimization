from simulation import Simulation, simulate, SimulationParams
from photovoltaic_module import SimpleEfficiencyModel
from utils import print_errors
import json


if __name__ == "__main__":

    # Inputs

    with open('../data/reference_sims/sam_pv_battery_4kwh.json', newline='') as file:
        data = json.load(file)

    address = data['address']
    model = data['model']
    load_profile = data['load_profile']
    sim_params = data['simulation_params']

    panel = SimpleEfficiencyModel(model)
    params = SimulationParams(**sim_params)

    # Simulations

    sim = Simulation(address=address, panel=panel, load_profile=load_profile, params=params, minute_modifer=+0.5)

    print("Annual load", sim.p_load.sum()/1000)

    lcoe = simulate(
        n_modules=data['n_modules'],
        c_nom=data['c_nom'],
        simulation=sim,
    )

    print_errors(data['results'], hyp=vars(sim.result))
