
class DummyBattery:
    def __init__(self, c_nom, bat_eff=0.92, min_soc=0.10, max_soc=0.95):
        self.c_nom = c_nom
        self.eff = bat_eff
        self.current_energy = c_nom * min_soc
        self.discharged = 0
        self.charged = 0
        self.charge_list = []
        self.min_soc = min_soc
        self.max_soc = max_soc

        # cycle count
        self.cycle_count = 0
        self._last_charge = 0
        self.cycle_begin = 0

        self.dischargedd = 0
        self.discharged_ls = []

    def cycle_update(self, charge):
        if self._last_charge != charge:
            if charge < 0:  # discharge
                self.cycle_count += 1
                self.cycle_begin = self.current_energy
            if charge > 0:  # charge
                self.discharged_ls.append(self.cycle_begin - self.current_energy)
                self.dischargedd += self.discharged_ls[-1]

        self._last_charge = charge

    def charge(self, energy):
        self.cycle_update(1)
        to_add = energy
        if to_add + self.current_energy > self.c_nom - (1 - self.max_soc) * self.c_nom:
            to_add = self.c_nom - self.current_energy - (1 - self.max_soc) * self.c_nom
        self.current_energy += to_add * self.eff
        self.charged += to_add

        self.charge_list.append(self.current_energy)
        return energy - to_add

    def discharge(self, energy):
        self.cycle_update(-1)
        to_discharge = energy
        if self.current_energy - self.min_soc * self.c_nom < to_discharge:
            to_discharge = self.current_energy - self.min_soc * self.c_nom

        assert energy >= to_discharge

        self.current_energy -= to_discharge
        self.discharged += to_discharge

        self.charge_list.append(self.current_energy)
        return energy - to_discharge

    def is_full(self):
        return self.c_nom <= self.current_energy

    def is_empty(self):
        return self.current_energy <= 0


# in case accurate number of cycles is important
def get_charge_periods(p_balance):
    res = []
    for day in range(365):
        day_ls = p_balance[day * 24:day * 24 + 24]

        charge_start = None
        charge_end = None

        for i in range(24):
            if day_ls[i] > 0:
                charge_start = i
                break

        for i in range(24):
            if day_ls[23 - i] > 0:
                charge_end = 23 - i
                break

        res.append((charge_start, charge_end))
    return res



