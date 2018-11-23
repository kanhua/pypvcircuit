import numpy as np
from pypvcell.solarcell import SQCell, MJCell, SolarCell
import yaml
from .quasi_3D_solver import create_node,create_header


def _load_solarcell_param(solarcell: SolarCell, param_name) -> np.array:
    import os
    this_dir=os.path.abspath(os.path.dirname(__file__))
    file = open(os.path.join(this_dir,"./default_circuit_param.yaml"), 'r')

    default_param = yaml.load(file)
    param = np.empty(len(solarcell.subcell))

    for i in range(len(solarcell.subcell)):
        if hasattr(solarcell.subcell[i], param_name):
            param[i] = getattr(solarcell.subcell[i], param_name)
        elif param_name in default_param.keys():
            param[i] = default_param[param_name]
        else:
            raise NotImplementedError("parameters not here")

    file.close()

    return param


class PixelProcessor(object):

    def __init__(self, solarcell: SQCell, lx, ly):
        print(len(solarcell.subcell))
        self.solarcell = solarcell
        self._cicuit_params = dict()
        self.lx = lx
        self.ly = ly
        self._set_circuit_params()

    def _set_circuit_params(self):
        raw_isc = _load_solarcell_param(self.solarcell, 'jsc')
        raw_i01 = _load_solarcell_param(self.solarcell, 'j01')
        raw_i02 = _load_solarcell_param(self.solarcell, 'j02')
        raw_rs_top = _load_solarcell_param(self.solarcell, 'rs_top')
        raw_rs_bot = _load_solarcell_param(self.solarcell, 'rs_bot')
        raw_r_series = _load_solarcell_param(self.solarcell, 'r_series')
        raw_r_shunt = _load_solarcell_param(self.solarcell, 'r_shunt')
        raw_r_contact = _load_solarcell_param(self.solarcell, 'r_contact')
        raw_r_line = _load_solarcell_param(self.solarcell, 'r_line')

        gn = np.sqrt(1.0 / raw_isc[0])

        area_per_pixel = self.lx * self.ly

        # TODO There are problems in this normalization

        self._cicuit_params['isc'] = raw_isc * area_per_pixel * gn
        #self._cicuit_params['i01'] = raw_i01 * area_per_pixel * gn
        #self._cicuit_params['i02'] = raw_i02 * area_per_pixel * gn
        self._cicuit_params['rs_top'] = raw_rs_top / gn
        self._cicuit_params['rs_bot'] = raw_rs_bot / gn
        self._cicuit_params['r_series'] = raw_r_series / area_per_pixel / gn
        self._cicuit_params['r_shunt'] = raw_r_shunt / area_per_pixel / gn
        self._cicuit_params['r_contact'] = raw_r_contact / area_per_pixel / gn
        #self._cicuit_params['r_metal'] = raw_r_line / gn
        self._cicuit_params['x_metal_top'] = raw_r_line / gn
        self._cicuit_params['y_metal_top'] = raw_r_line / gn

    def node_string(self):
        return create_node("normal", idx=0, idy=0, Lx=self.lx, Ly=self.ly,
                           **self._cicuit_params)


if __name__ == "__main__":
    sq = SQCell(1.42, 300, 1)
    from pypvcell.illumination import load_astm

    ill = load_astm("AM1.5g")
    sq.set_input_spectrum(ill)
    px = PixelProcessor(sq, lx=1e-6, ly=1e-6)
