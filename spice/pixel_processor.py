import numpy as np
from pypvcell.solarcell import SQCell, MJCell, SolarCell
import yaml


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

    def __init__(self, solarcell: SQCell, lr, lc, h, gn=1):
        self.solarcell = solarcell
        self._cicuit_params = dict()
        self.lr = lr
        self.lc = lc
        self.finger_h = h
        self.gn = gn
        self._set_circuit_params()

    def _set_circuit_params(self):
        self.raw_isc = _load_solarcell_param(self.solarcell, 'jsc')
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

        self.area_per_pixel = self.lr * self.lc

        # TODO There are problems in this normalization

        self._cicuit_params['isc'] = self.raw_isc * self.area_per_pixel * self.gn
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

        self.r_line = self.rho_metal / self.rho_metal / self.gn

        # TODO threshold of metal value
        self.metal_threshold = 0

    def header_string(self, pw):

        # TODO patch pw:

        self.i01 = self.raw_i01 * self.area_per_pixel * pw * pw * self.gn
        self.i02 = self.raw_i02 * self.area_per_pixel * pw * pw * self.gn

        return create_header(I01=self.i01, I02=self.i02, n1=self.n1, n2=self.n2, Eg=self.eg)

    def diode_string(self, id_r, id_c, pw):

        # TODO now assuming pw_c=pw_r

        diode_string = ""

        self.i01 = self.raw_i01 * self.area_per_pixel * pw * pw * self.gn
        self.i02 = self.raw_i02 * self.area_per_pixel * pw * pw * self.gn

        for j in range(self.i01.size):
            modelDiode1 = ".model diode1_{0}_{4}_{5} d(is={1},n={2},eg={3})\n".format(j, self.i01[j], self.n1[j],
                                                                                      self.eg[j], id_r, id_c)
            modelDiode2 = ".model diode2_{0}_{4}_{5} d(is={1},n={2},eg={3})\n".format(j, self.i02[j], self.n2[j],
                                                                                      self.eg[j], id_r, id_c)
            diode_string += modelDiode1
            diode_string += modelDiode2

        return diode_string

    def node_string(self, id_r, id_c, sub_image, is_boundary_r=False, is_boundary_c=False):

        assert sub_image.size > 0

        diode_string = self.diode_string(id_r, id_c, sub_image.shape[0])

        r_metal_row, r_metal_col, metal_coverage = \
            get_pixel_r(sub_image, r_row=self.r_line, r_col=self.r_line, threshold=self.metal_threshold)

        merged_pixel_lc = sub_image.shape[1] * self.lc
        merged_pixel_lr = sub_image.shape[0] * self.lr

        merged_pixel_area = merged_pixel_lc * merged_pixel_lr

        self._cicuit_params['isc'] = self.raw_isc * self.lc * self.lr * self.gn

        if metal_coverage > self.metal_threshold:
            agg_contact = self.r_contact / (merged_pixel_area * metal_coverage) / self.gn
            # TODO quick fix on distinguish bus bar and finger
            if np.max(sub_image) > 250:
                type = 'Bus'
            else:
                type = 'Finger'
        else:
            agg_contact = np.inf
            type = 'Normal'

        node_string = create_node(type, idr=id_r, idc=id_c, l_r=merged_pixel_lr, l_c=merged_pixel_lc,
                                  r_metal_top_r=r_metal_row, r_metal_top_c=r_metal_col, r_contact=agg_contact,
                                  boundary_r=is_boundary_r, boundary_c=is_boundary_c, **self._cicuit_params)

        return diode_string + node_string


def create_node(type, idr, idc, l_r, l_c, isc, rs_top, rs_bot,
                r_shunt, r_series, r_metal_top_r, r_metal_top_c, r_contact,
                boundary_r=False, boundary_c=False):
    """ Creates a node of the solar cell, meaning all the circuit elements at an XY location in the plane.
    This includes all the diodes, resistances and current sources for all the junctions at that location.

    :param type: The type of the node, 'Normal', 'Finger' or 'Bus'
    :param idr: row index, idr-th row
    :param idc: column index, idc-th row
    :param l_r: Pixel size in the row direction
    :param l_c: Pixel size in the column direction
    :param isc: Array of Isc for each of the junctions
    :param rs_top: Array of resistances of the top lateral conductive layer
    :param rs_bot: Array of resistances of the bottom lateral conductive layers
    :param r_shunt: Array of Rshunt for each of the junctions
    :param r_series: Array of Rseries for each of the junctions
    :param r_metal_top_r: Resistance of the metal in the X direction
    :param r_metal_top_c: Resistance of the metal in the Y direction
    :param r_contact: Contact resistance
    :param boundary_r: boolean value. True if this node is the last node in a row
    :param boundary_c: boolean value. True if this node is the last node in a column
    :return: The node define in SPICE file as a string.
    """
    node = ''
    for j in range(len(isc)):
        # using zfill
        loc = str(j) + "_" + str(idr).zfill(3) + "_" + str(idc).zfill(3)
        loc_row_neighbor = str(j) + "_" + str(idr + 1).zfill(3) + "_" + str(idc).zfill(3)
        loc_column_neighbor = str(j) + "_" + str(idr).zfill(3) + "_" + str(idc + 1).zfill(3)

        if j + 1 == len(isc):
            locLow = 0
        else:
            locLow = "t_" + str(j + 1) + "_" + str(idr).zfill(3) + "_" + str(idc).zfill(3)

        s = l_c / l_r

        # We add the diodes
        diode1 = "d1_{0} t_{0} b_{0} diode1_{1}_{2}_{3}\n".format(loc, j, idr, idc)
        # diode2 = "d2_{0} t_{0} b_{0} diode2_{1}\n".format(loc, j)

        # TODO: patch 1
        diode2 = ""

        # Now the shunt resistance
        rshuntJ = "Rshunt_{0} t_{0} b_{0} {1}\n".format(loc, r_shunt[j])

        # TODO: patch 2
        rshuntJ = ""

        # And add the source
        source = 'i{0} b_{0} t_{0} {1}\n'.format(loc, isc[j])

        rbotLCLX = ""
        rtopLCLX = ""

        rbotLCLY = ""
        rtopLCLY = ""

        if not boundary_r:
            # Now we add the sheet resistances
            rbotLCLX = "RbX{0}to{1} b_{0} b_{1} {2}\n".format(loc, loc_row_neighbor, rs_bot[j] / s)
            rtopLCLX = "RtX{0}to{1} t_{0} t_{1} {2}\n".format(loc, loc_row_neighbor, rs_top[j] / s)

        if not boundary_c:
            rbotLCLY = "RbY{0}to{1} b_{0} b_{1} {2}\n".format(loc, loc_column_neighbor, rs_bot[j] * s)
            rtopLCLY = "RtY{0}to{1} t_{0} t_{1} {2}\n".format(loc, loc_column_neighbor, rs_top[j] * s)

        # Now the series resistance with the back of the junction
        rseriesJ = "Rseries{0}to{1} b_{0} {1} {2}\n".format(loc, locLow, r_series[j])

        # TODO: patch 3

        rseriesJ = "Rseries{0}to{1} b_{0} {1} {2}\n".format(loc, locLow, 0)

        # TODO temporarily disabled r_metal_top_r and r_metal_top_c
        # r_metal_top_r = 0
        # r_metal_top_c = 0

        # TODO disable sheet resistance
        # rbotLCLX = ""
        # rtopLCLX = ""

        # rbotLCLY = ""
        # rtopLCLY = ""

        if j == 0 and type == 'Finger':
            rcontact = "Rcontact{0} t_{0} m_{0} {1}\n".format(loc, r_contact)
            rmetalX = "RbusX{0}to{1} m_{0} m_{1} {2}\n".format(loc, loc_row_neighbor, r_metal_top_r)
            rmetalY = "RbusY{0}to{1} m_{0} m_{1} {2}\n".format(loc, loc_column_neighbor, r_metal_top_c)
            rext = ""

        elif j == 0 and type == 'Bus':
            rcontact = "Rcontact{0} t_{0} m_{0} {1}\n".format(loc, r_contact)
            rmetalX = "RbusX{0}to{1} m_{0} m_{1} {2}\n".format(loc, loc_row_neighbor, r_metal_top_r)
            rmetalY = "RbusY{0}to{1} m_{0} m_{1} {2}\n".format(loc, loc_column_neighbor, r_metal_top_c)

            # This is the connection to the external voltage
            # TODO: this value wasn't normalized with gn
            rext = "Rext{0} in m_{0} {1}\n".format(loc, 0)

        else:
            rcontact = ""
            rmetalX = ""
            rmetalY = ""
            rext = ""

        # Finally, we create the output statement for this node
        if j == 0 and type in ['Finger', 'Bus']:
            output = ".PRINT DC v(t_{0}) v(b_{0}) v(m_{0})\n\n".format(loc)
        else:
            output = ".PRINT DC v(t_{0}) v(b_{0})\n\n".format(loc)

        # and put all the instructions together
        node = node + diode1 + diode2 + source + rshuntJ + rtopLCLX + rtopLCLY + rbotLCLX + rbotLCLY + rseriesJ + \
               rcontact + rmetalX + rmetalY + rext + output

    return node


def create_header(I01, I02, n1, n2, Eg, T=20):
    """ Creates the header of the SPICE file, where the diode models, the temperature and the independent voltage source are defined.

    :param I01: Array of I01 for each of the junctions
    :param I02: Array of I02 for each of the junctions
    :param n1: Array of n1 for each of the junctions
    :param n2: Array of n2 for each of the junctions
    :param Eg: Array of Eg for each of the junctions
    :param T: Temperature of the device
    :return: The header of the SPICE file as a string.
    """
    title = "*** A SPICE simulation with python\n\n"

    diodes = ""
    for j in range(len(I01)):
        modelDiode1 = ".model diode1_{0} d(is={1},n={2},eg={3})\n".format(j, I01[j], n1[j], Eg[j])
        modelDiode2 = ".model diode2_{0} d(is={1},n={2},eg={3})\n".format(j, I02[j], n2[j], Eg[j])

        diodes = diodes + modelDiode1 + modelDiode2

    options = ".OPTIONS TNOM=20 TEMP={0}\n\n".format(T)
    independent_source = """ 
    vdep in 0 DC 0
    """

    SPICEheader = title + diodes + options + independent_source

    return SPICEheader


if __name__ == "__main__":
    sq = SQCell(1.42, 300, 1)
    from pypvcell.illumination import load_astm

    ill = load_astm("AM1.5g")
    sq.set_input_spectrum(ill)
    px = PixelProcessor(sq, lr=1e-6, lc=1e-6)


def get_pixel_r(image: np.ndarray, r_row, r_col, threshold):
    """
    Calculate the aggregated resistance from a mask profile image

    :param image: an ndarray matrix
    :param r_col: resistance value per pixel in x-direction (columns, dim=1)
    :param r_row: resistance value per pixel in y-direction (rows, dim=0)
    :param threshold: threshold value of a pixel that it is a metal
    :return: aggregated resistance in x, resistance in y, metal coverage ratio
    """

    assert image.ndim == 2

    r_mask = np.where(image > threshold, 1, 0)

    # corner case
    if np.sum(r_mask) == 0:
        return np.inf, np.inf, 0

    metal_coverage_ratio = np.sum(r_mask).astype(np.float) / (image.shape[0] * image.shape[1])

    row_sum = np.sum(r_mask, axis=0)
    row_sum_mask = np.where(row_sum == 0, np.inf, 0)
    row_sum = row_sum_mask + row_sum

    agg_r_row = 1 / np.sum(1 / (row_sum * r_row))

    col_sum = np.sum(r_mask, axis=1)
    col_sum_mask = np.where(col_sum == 0, np.inf, 0)
    col_sum = col_sum_mask + col_sum

    agg_r_col = 1 / np.sum(1 / (col_sum * r_col))

    return agg_r_col, agg_r_row, metal_coverage_ratio
