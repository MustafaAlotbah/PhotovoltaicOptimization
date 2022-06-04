from ._financial_model import get_total_cost, get_cnom
import numpy as np
from .interface import Simulation


def get_num_panels_per_surface(
        num_panels,
        ids_by_mean_irr,
        max_panels_per_surface,
):
    panels_per_surface = [0 for _ in range(len(ids_by_mean_irr))]

    for i in range(len(panels_per_surface)):
        panel_id = ids_by_mean_irr[i]
        _max = max_panels_per_surface[panel_id]

        panels_per_surface[panel_id] = min(_max, num_panels)

        num_panels = num_panels - _max

        if num_panels <= 0:
            break

    return panels_per_surface


def get_p_max(p_maxs, panels_per_surface) -> np.array:
    num_surfaces = p_maxs.shape[0]

    p_max = np.zeros(shape=p_maxs.shape[1:])

    for i in range(num_surfaces):
        p_max += panels_per_surface[i] * p_maxs[i]

    return p_max


def get_energy_yield_c0(p_load, p_balance):
    energy_yield_c0 = np.array([
        [-p if p < 0 else 0 for p in p_day] for p_day in p_balance
    ])
    energy_to_load = p_load - energy_yield_c0
    return energy_to_load


def get_energy_distributions(energy_balance, num_classes=100):
    surplus_daily_energy = [sum([energy for energy in day if energy >= 0]) for day in energy_balance]
    deficit_daily_energy = [sum([energy for energy in day if energy < 0]) for day in energy_balance]

    max_surplus = max(surplus_daily_energy)
    max_deficit = -min(deficit_daily_energy)

    surplus_distribution = [0 for _ in range(num_classes)]
    surplus_classes = [max_surplus * (i + 0.3) / num_classes for i in range(num_classes)]

    deficit_distribution = [0 for _ in range(num_classes)]
    deficit_classes = [max_deficit * (i + 0.3) / num_classes for i in range(num_classes)]

    for class_num in range(num_classes):
        floor_energy_surplus = max_surplus * class_num / num_classes
        ceil_energy_surplus = max_surplus * (class_num+1) / num_classes

        floor_energy_deficit = max_deficit * class_num / num_classes
        ceil_energy_deficit = max_deficit * (class_num+1) / num_classes

        for day in range(365):
            # surplus
            if floor_energy_surplus <= surplus_daily_energy[day] < ceil_energy_surplus+1:
                surplus_distribution[class_num] += 1/365

            # deficit
            if floor_energy_deficit <= -deficit_daily_energy[day] < ceil_energy_deficit+1:
                deficit_distribution[class_num] += 1/365

    return surplus_distribution, surplus_classes, deficit_distribution, deficit_classes


def simulate(
        n_modules: float,
        c_nom: float,
        simulation: Simulation,
) -> float:

    """
    Start a simulation for a simulation object.
    :param n_modules: Number of modules, float to make the optimization process smooth
    :param c_nom: The battery's capacity in [Wh]
    :param simulation: The simulation object
    """

    if n_modules <= 0:
        return simulation.params.cost_kwh_grid

    num_surfaces = len(simulation.max_panels_per_surface)
    assert num_surfaces >= max(simulation.ids_by_annual_irr)

    # assign panels per surface starting with the surfaces with maximum incident radiation
    panels_per_surface = get_num_panels_per_surface(
        n_modules,
        simulation.ids_by_annual_irr,
        simulation.max_panels_per_surface
    )

    simulation.result.p_dc_hourly = get_p_max(simulation.p_maxs, panels_per_surface)
    simulation.result.p_ac_hourly = simulation.result.p_dc_hourly * simulation.params.inverter_eff
    simulation.result.p_balance_hourly = simulation.result.p_ac_hourly - simulation.p_load
    simulation.result.energy_dc_annually = simulation.result.p_dc_hourly.sum()/1000
    simulation.result.energy_ac_annually = simulation.result.p_ac_hourly.sum()/1000

    p_surplus, e_surplus, p_deficit, e_deficit = get_energy_distributions(simulation.result.p_balance_hourly)

    simulation.result.p_pv2load_hourly = get_energy_yield_c0(
        simulation.p_load,
        simulation.result.p_balance_hourly
    )

    simulation.result.energy_pv2load_annually = simulation.result.p_pv2load_hourly.sum()/1000

    get_total_cost(
        c_nom=c_nom,
        n_modules=n_modules,
        p_surplus=p_surplus,
        e_surplus=e_surplus,
        simulation=simulation,
    )

    simulation.result.self_consumption = (
                                                 simulation.result.energy_pv2load_annually +
                                                 simulation.result.energy_pv2bess_annually
                                         ) / simulation.result.energy_ac_annually

    simulation.result.equity = simulation.panel.cost * n_modules + \
                               get_cnom(
                                   c_nom,
                                   simulation.params.cost_bat_kwh,
                                   simulation.result.lifetime_bess
                               ) * \
                               c_nom / 1000 + \
                               simulation.params.additional_costs



    # flatten variables
    simulation.result.p_dc_hourly = simulation.result.p_dc_hourly.flatten().tolist()
    print(simulation.result.p_dc_hourly )
    simulation.result.p_ac_hourly = simulation.result.p_ac_hourly.flatten().tolist()
    simulation.result.p_pv2load_hourly = simulation.result.p_pv2load_hourly.flatten().tolist()
    simulation.result.p_balance_hourly = simulation.result.p_balance_hourly.flatten().tolist()

    simulation.result.annual_costs_with_system = simulation.p_load.sum()/1000 * simulation.result.lcoe
    simulation.result.annual_savings = simulation.p_load.sum()/1000 * simulation.params.cost_kwh_grid - simulation.result.net_annual_bill_annually
    simulation.result.return_on_investment = simulation.result.annual_savings / simulation.result.equity

    return simulation.result.lcoe
