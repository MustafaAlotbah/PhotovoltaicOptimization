from .utils import *
import numpy as np


class UndefinedPhotovoltaicModelException(Exception):
    pass


# This is an interface of a photovoltaic model
class PhotovoltaicModel:
    default_cost_per_kwh = 1400
    default_panel_width = 1
    default_panel_height = 1.63

    def __init__(self, specs):
        self.mpp_ref = specs['mpp']
        self.cost = specs['cost'] if 'cost' in specs.keys() else \
            PhotovoltaicModel.default_cost_per_kwh/1000*self.mpp_ref
        self.width = specs['width'] if 'width' in specs.keys() else \
            PhotovoltaicModel.default_panel_width
        self.height = specs['height'] if 'height' in specs.keys() else \
            PhotovoltaicModel.default_panel_height

    def get_mpp(self, t: float, g: float, vw: float) -> float:
        raise UndefinedPhotovoltaicModelException("The model has to be a valid Photovoltaic model!")


# this is a valid model
class SimpleEfficiencyModel(PhotovoltaicModel):
    def __init__(self, specs: dict, num_panels=1):
        super(SimpleEfficiencyModel, self).__init__(specs)
        self.mu_p = specs['mu_mpp'] * 1e-2
        self.num_panels = num_panels
        self.t_ref = specs['T_ref'] if 'T_ref' in specs.keys() else 298.15
        self.t_noct = specs['T_NOCT'] if 'T_NOCT' in specs.keys() else 273.15 + 41


        #
        self.sandia_params = {
            'a': -3.56,
            'b': -0.075,
            'dt': 3
        }

    def get_mpp_iv(self, t, g):
        return self.mpp_ref * g / 1000 * (1 + self.mu_p * (t - self.t_ref)), 1

    def get_cell_t(self, t_amb, g, vw=0, method="sandia"):
        if method == "sandia":
            return t_amb + g * (
                    np.exp(self.sandia_params['a'] + self.sandia_params['b'] * vw)
                    + self.sandia_params['dt']/1000
            )
        # Masters 2004
        return t_amb + (self.t_noct - celsius2kelvin(20)) / 0.8 * g / 1000

    def get_mpp(self, t, g, vw):
        cell_temperature = self.get_cell_t(273.15 + t, g, vw)
        v, i = self.get_mpp_iv(cell_temperature, g)
        return v * i




