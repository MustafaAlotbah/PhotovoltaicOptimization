import numpy as np
from .battery import simulate_battery
from .interface import Simulation


# capital recovery factor
def calc_crf(n, dr, inflation_rate=0):
    i = (1 + dr) * (1 + inflation_rate) - 1
    if i == 0:
        return 1/n
    a = (1 + i)**n
    return i * a / (a - 1)


# net present value coefficient
def calc_npv(n, dr, inflation_rate=0, step=1):
    i = (1 + dr) * (1 + inflation_rate) - 1
    return sum([(1 + inflation_rate)**(t-1) / (1 + i)**t for t in range(1, n + 1, step)])


# dod [5..100]
# d [0.5 .. 1.25]
# Cyclic lifetime of a battery
def get_n_cyc(dod, d=1):
    dod /= 100              # [0.05 .. 1]
    dod = max(dod, 0.1)

    b0 = 1036
    b1 = 0.5618
    b2 = 1.7957
    return (b0 * dod**-b1 * np.exp(b2 * (1 - dod)))/d


def get_dod(i, c_nom, e_surplus):
    return min(e_surplus[i]/c_nom, 1)


def get_n_cyc_i(i, c_nom, e_surplus):
    dod = get_dod(i, c_nom, e_surplus) * 100
    return get_n_cyc(dod)


def get_n_cycle_life(c_nom, p_surplus, e_surplus, n_cal=25*365.25):
    return sum([p_surplus[i] * min(n_cal, get_n_cyc_i(i, c_nom, e_surplus)) for i in range(len(p_surplus))])


def get_n_cycle_life_year(c_nom, p_surplus, e_surplus):
    res = get_n_cycle_life(c_nom, p_surplus, e_surplus)/365.25
    return res


def mean_energy_stored_daily(c_nom, p_surplus, e_surplus):
    return np.array([
        p_surplus[i] * min(e_surplus[i], c_nom * get_dod(i, c_nom, e_surplus)) for i in range(len(p_surplus))
    ])


def annual_energy_stored_kwh(mean_energy_stored_daily):
    return 365.25 * mean_energy_stored_daily.sum() / 1000


def annual_energy_stored_kwh_eff(c_nom, p_surplus, e_surplus, bat_eff=0.92):
    res = 365.25 * mean_energy_stored_daily(c_nom, p_surplus, e_surplus).sum() / 1000 * bat_eff
    return res


def get_cnom_price_by_year(cost_bat_kwh, lifetime, annual_decrease_rate):
    lifetime = np.floor(lifetime)+1
    R = [cost_bat_kwh * (1 - annual_decrease_rate) ** (i // lifetime * lifetime) for i in range(25)]
    if len(R) == 0:
        return 0
    return sum(R)/25


def get_cnom(c_nom, cost_bat_kwh, lifetime, annual_decrease_rate=0.08):
    if c_nom > 16000:  # maximum of linear regression model
        c_nom = 16000
    if lifetime < 1:
        return 0
    capacity_adjsuted = cost_bat_kwh * (1.0249406176 - 0.0249406176 * c_nom/1000)

    a = get_cnom_price_by_year(capacity_adjsuted, lifetime, annual_decrease_rate)
    b = get_cnom_price_by_year(capacity_adjsuted, lifetime+1, annual_decrease_rate)

    p = lifetime % 1

    return a * (1-p) + b * (p)


def cost_stored_energy(
        c_nom,
        energy_stored,
        p_surplus,
        e_surplus,
        simulation: Simulation,
) -> None:
    if c_nom < 5 or energy_stored <= 0:
        simulation.result.lcoe_bess = 0
        simulation.result.lifetime_bess = 0
        simulation.result.c_nom_cost = 0
        return

    num_years = get_n_cycle_life_year(c_nom, p_surplus, e_surplus)

    f = calc_crf(num_years+1.0, dr=simulation.params.battery_discount_rate, inflation_rate=simulation.params.inflation_rate)

    cost_bat_kwh_adjusted = get_cnom(c_nom, simulation.params.cost_bat_kwh, num_years)

    simulation.result.lcoe_bess = cost_bat_kwh_adjusted * c_nom / 1000 * f / energy_stored
    simulation.result.lifetime_bess = num_years
    simulation.result.c_nom_cost = cost_bat_kwh_adjusted


def calc_lcoe_pv(
        n_modules,
        module_cost,
        pv_output_ac,
        pv_lifetime=25,
        maintenance=0.015,
        pv_discount_rate=4e-2,
        inflation_rate=0,
        annual_follow_on_costs=0,         # e.g. O&M
        additional_costs=0,               # e.g. inverter

):
    modules_cost = n_modules * module_cost

    crf = calc_crf(pv_lifetime, dr=pv_discount_rate, inflation_rate=inflation_rate)
    npv_f = calc_npv(pv_lifetime, dr=pv_discount_rate, inflation_rate=inflation_rate)

    num = modules_cost + additional_costs \
          + (annual_follow_on_costs + maintenance * modules_cost) * npv_f

    res = num / pv_output_ac * crf
    # print("LCOE, CRF", crf)
    return res


def get_sufficiency(energy_stored, energy_yield_c0, total_load):
    return (energy_stored + energy_yield_c0) / total_load


def get_sufficiency_by_c_nom(c_nom, p_surplus, e_surplus, energy_yield, total_load, bat_eff=0.92):
    energy_stored = annual_energy_stored_kwh_eff(c_nom, p_surplus, e_surplus, bat_eff=bat_eff)
    return get_sufficiency(energy_stored, energy_yield, total_load)


def calc_lcoes(
        p_surplus,
        e_surplus,
        n_modules: float,
        c_nom: float,
        simulation: Simulation,
) -> None:
    cost_stored_energy(
        c_nom,
        simulation.result.energy_pv2bess_annually,
        p_surplus,
        e_surplus,
        simulation=simulation
    )

    simulation.result.lcoe_pv = calc_lcoe_pv(
        n_modules=n_modules,
        module_cost=simulation.panel.cost,
        pv_output_ac=simulation.result.energy_ac_annually,
        pv_lifetime=simulation.params.pv_lifetime,
        maintenance=simulation.params.maintenance,
        pv_discount_rate=simulation.params.pv_discount_rate,
        inflation_rate=simulation.params.inflation_rate,
        annual_follow_on_costs=simulation.params.annual_follow_on_costs,
        additional_costs=simulation.params.additional_costs,
    )


def get_annual_bill(total_load, energy_yield_c0, bat_discharged, cost_kwh_grid):
    bill = (total_load - energy_yield_c0 - bat_discharged) * cost_kwh_grid
    return bill


def get_total_cost(
        c_nom: float,
        n_modules: float,
        p_surplus: np.array,
        e_surplus: np.array,
        simulation: Simulation
) -> None:

    simulate_battery(
        c_nom, simulation
    )

    calc_lcoes(
        p_surplus, e_surplus,
        n_modules,
        c_nom,
        simulation=simulation,
    )

    annual_load_kwh = simulation.p_load.sum()/1000

    simulation.result.self_sufficiency = get_sufficiency(simulation.result.energy_bess2load_annually, simulation.result.energy_pv2load_annually, annual_load_kwh)

    # annual bill with system before compensation
    annual_bill = get_annual_bill(annual_load_kwh, simulation.result.energy_pv2load_annually, simulation.result.energy_bess2load_annually, cost_kwh_grid=simulation.params.cost_kwh_grid)

    simulation.result.energy_pv_bess2load_annually = simulation.result.energy_bess2load_annually + simulation.result.energy_pv2load_annually

    simulation.result.energy_grid2load_annually  = annual_load_kwh - simulation.result.energy_pv_bess2load_annually

    # annual bill with system after compensation (import - export)
    simulation.result.net_annual_bill_annually = annual_bill - simulation.result.grid_compensation_total

    simulation.result.cost_annual_bess = simulation.result.lcoe_bess * simulation.result.energy_bess2load_annually
    simulation.result.cost_annual_pv = simulation.result.lcoe_pv * simulation.result.energy_ac_annually

    simulation.result.lcoe = (simulation.result.net_annual_bill_annually + simulation.result.cost_annual_bess + simulation.result.cost_annual_pv) / annual_load_kwh

    simulation.result.energy_bess_loss_annually = simulation.result.energy_pv2bess_annually - simulation.result.energy_bess2load_annually














