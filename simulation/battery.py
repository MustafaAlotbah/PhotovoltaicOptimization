import battery
from .interface import Simulation

days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def simulate_battery(c_nom: float, simulation: Simulation) -> None:
    p_balance = simulation.result.p_balance_hourly.flatten()
    p_load = simulation.p_load.flatten()

    bat = battery.DummyBattery(
        c_nom,
        bat_eff=simulation.params.bat_eff,
        min_soc=simulation.params.min_soc,
        max_soc=simulation.params.max_soc
    )

    schedule = battery.get_charge_periods(p_balance)

    grid_meter_buy = 0
    grid_meter_sell = 0

    grid_meter_sell_month = []
    grid_compensation_month = []
    grid_compensation_month_adjusted = []

    bat_charge_ls = []
    bat_to_load_ls = []
    bat_to_load_ls_monthly = []

    h = -1
    d = -1
    for month in range(len(days_in_month)):
        bat_to_load_this_month = []
        for day in range(days_in_month[month]):
            d += 1
            for hour in range(24):
                h += 1
                if p_balance[h] > 0:
                    bat_to_load_ls.append(0)
                    if bat.is_full():
                        grid_meter_sell += p_balance[h]
                    else:
                        leftover = bat.charge(p_balance[h])
                        assert leftover >= 0
                        grid_meter_sell += leftover

                elif p_balance[h] < 0:
                    # if bat.isEmpty() or (schedule[d][0] and schedule[d][0] <= hour <= schedule[d][1]):
                    # if bat.isEmpty() or (6 <= hour <= 18):
                    if bat.is_empty():
                        grid_meter_buy -= p_balance[h]
                        bat_to_load_ls.append(0)
                    else:
                        leftover = bat.discharge(-p_balance[h])
                        bat_to_load_ls.append(-p_balance[h] - leftover)
                        grid_meter_buy += leftover

                bat_to_load_this_month.append(bat_to_load_ls[-1])

                bat_charge_ls.append(bat.current_energy)

        bat_to_load_ls_monthly.append(sum(bat_to_load_this_month)/1000)

        grid_meter_sell_month.append(grid_meter_sell - sum(grid_meter_sell_month))

        grid_compensation_month.append(grid_meter_sell_month[-1] / 1000 * simulation.params.c_feedin0_kwh)

        # calculate monthly compensation
        this_month_sell_energy = grid_meter_sell_month[-1] / 1000
        this_month_output = (p_load + p_balance)[sum(days_in_month[:month])*24:sum(days_in_month[:month+1])*24].sum()/1000
        this_month_self_consumption = 1 - this_month_sell_energy / this_month_output

        this_month_compensation = this_month_sell_energy * 0.7 * simulation.params.c_feedin0_kwh * (1 - simulation.params.i_feedin_monthly) ** month
        if this_month_self_consumption >= 0.3:
            this_month_compensation = this_month_sell_energy * simulation.params.c_feedin0_kwh * (1 - simulation.params.i_feedin_monthly) ** month

        grid_compensation_month_adjusted.append(this_month_compensation)


    # end of month

    grid_compensation_total = sum(grid_compensation_month_adjusted)
    energy_pv2grid_annually = sum(grid_meter_sell_month)

    simulation.result.bat_soc_hourly = [x / bat.c_nom * 100 for x in bat_charge_ls] if bat.c_nom > 0 else None

    simulation.result.p_bat2load_hourly = [i for i in bat_to_load_ls]
    simulation.result.energy_pv2grid_annually = energy_pv2grid_annually/1000
    simulation.result.grid_compensation_total = grid_compensation_total
    simulation.result.energy_bess2load_annually = bat.discharged/1000
    simulation.result.energy_pv2bess_annually = bat.charged/1000

