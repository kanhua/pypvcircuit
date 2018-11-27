import numpy as np
from pypvcell.solarcell import SQCell, MJCell, SolarCell
import yaml
from .quasi_3D_solver import create_node, create_header
from .dynamic_pixel import get_pixel_r


def _load_solarcell_param(solarcell: SolarCell, param_name) -> np.array:
    import os
    this_dir = os.path.abspath(os.path.dirname(__file__))
    file = open(os.path.join(this_dir, "./default_circuit_param.yaml"), 'r')

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

    def __init__(self, solarcell: SQCell, lx, ly, h):
        self.solarcell = solarcell
        self._cicuit_params = dict()
        self.lx = lx
        self.ly = ly
        self.finger_h=h
        self._set_circuit_params()

    def _set_circuit_params(self):
        raw_isc = _load_solarcell_param(self.solarcell, 'jsc')
        self.raw_i01 = _load_solarcell_param(self.solarcell, 'j01')
        self.raw_i02 = _load_solarcell_param(self.solarcell, 'j02')
        raw_rs_top = _load_solarcell_param(self.solarcell, 'rs_top')
        raw_rs_bot = _load_solarcell_param(self.solarcell, 'rs_bot')
        raw_r_series = _load_solarcell_param(self.solarcell, 'r_series')
        raw_r_shunt = _load_solarcell_param(self.solarcell, 'r_shunt')

        # TODO monkey patch, _load_solarcell_param assumes the
        # every parameter belongs to a junction
        self.r_contact = _load_solarcell_param(self.solarcell, 'r_contact')[0]
        self.rho_metal = _load_solarcell_param(self.solarcell, 'rho_metal')[0]

        self.eg = _load_solarcell_param(self.solarcell, 'eg')
        self.n1 = _load_solarcell_param(self.solarcell, 'n1')
        self.n2 = _load_solarcell_param(self.solarcell, 'n2')

        # TODO use dummy isc: because isc is not universal in every pixel
        self.gn = np.sqrt(1.0 / 340)
        # TODO temporarily disable gn
        #self.gn = 1

        self.area_per_pixel = self.lx * self.ly

        # TODO There are problems in this normalization

        self._cicuit_params['isc'] = raw_isc * self.area_per_pixel * self.gn
        # self._cicuit_params['i01'] = raw_i01 * area_per_pixel * gn
        # self._cicuit_params['i02'] = raw_i02 * area_per_pixel * gn
        self._cicuit_params['rs_top'] = raw_rs_top / self.gn
        self._cicuit_params['rs_bot'] = raw_rs_bot / self.gn
        self._cicuit_params['r_series'] = raw_r_series / self.area_per_pixel / self.gn
        self._cicuit_params['r_shunt'] = raw_r_shunt / self.area_per_pixel / self.gn
        # self._cicuit_params['r_contact'] = raw_r_contact / area_per_pixel / gn
        # self._cicuit_params['r_metal'] = raw_r_line / gn
        # self._cicuit_params['x_metal_top'] = raw_r_line / gn
        # self._cicuit_params['y_metal_top'] = raw_r_line / gn


        self.r_line = self.rho_metal/ self.rho_metal / self.gn


        # TODO threshold of metal value
        self.metal_threshold = 0

    def header_string(self,pw):

        #TODO patch pw:

        self.i01 = self.raw_i01 * self.area_per_pixel*pw*pw * self.gn
        self.i02 = self.raw_i02 * self.area_per_pixel *pw*pw* self.gn


        return create_header(I01=self.i01, I02=self.i02, n1=self.n1, n2=self.n2, Eg=self.eg)

    def node_string(self,  idx, idy, sub_image, lx, ly, is_boundary_x=False,is_boundary_y=False):

        assert sub_image.size > 0

        meta_r_x, metal_r_y, metal_coverage = \
            get_pixel_r(sub_image, r_x=self.r_line, r_y=self.r_line, threshold=self.metal_threshold)

        merged_pixel_lx = sub_image.shape[1] * lx
        merged_pixel_ly = sub_image.shape[0] * ly

        merged_pixel_area = merged_pixel_lx * merged_pixel_ly

        if metal_coverage > self.metal_threshold:
            agg_contact = self.r_contact / (merged_pixel_area * metal_coverage) / self.gn
            type='Bus'
        else:
            agg_contact = np.inf
            type='Normal'

        return create_node(type, idx=idx, idy=idy, Lx=self.lx, Ly=self.ly,
                           x_metal_top=merged_pixel_lx,
                           y_metal_top=merged_pixel_ly, r_contact=agg_contact,
                           boundary_x=is_boundary_x,boundary_y=is_boundary_y,
                           **self._cicuit_params)


if __name__ == "__main__":
    sq = SQCell(1.42, 300, 1)
    from pypvcell.illumination import load_astm

    ill = load_astm("AM1.5g")
    sq.set_input_spectrum(ill)
    px = PixelProcessor(sq, lx=1e-6, ly=1e-6)
