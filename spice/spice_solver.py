import typing
import numpy as np
from .dynamic_pixel import iterate_sub_image, resize_illumination, get_pixel_r
from .pixel_processor import PixelProcessor
from .spice import solve_circuit
from .parse_spice_output import parse_output
from pypvcell.solarcell import SQCell, SolarCell
from pypvcell.illumination import load_astm


class SinglePixelSolver(object):

    def __init__(self, solarcell: SolarCell, illumination, v_start,
                 v_end, v_steps, Lx, Ly, h, spice_preprocessor=None):
        self.solarcell = solarcell

        self.lx = Lx
        self.ly = Ly
        self.finger_h = h
        self.illumination = illumination

        self.v_start = v_start
        self.v_end = v_end
        self.v_steps = v_steps

        self.V = None
        self.I = None

        self.spice_preprocessor = spice_preprocessor

        header = self._generate_header()
        nodes = self._generate_network()
        exec = self._generate_exec()
        spice_footer = ".end"

        self.spice_input = header + nodes + exec + spice_footer

        self.raw_results = self._send_command()

        self._parse_output()

    def _generate_network(self):
        dummy_image = np.array([[1]])

        self.solarcell.set_input_spectrum(load_astm("AM1.5g") * self.illumination)

        px = PixelProcessor(self.solarcell, self.lx, self.ly, h=self.finger_h)
        return px.node_string(idx=0, idy=0,
                              sub_image=dummy_image, lx=self.lx, ly=self.ly, is_boundary_x=True, is_boundary_y=True)

    def _generate_header(self):
        px = PixelProcessor(self.solarcell, lx=self.lx, ly=self.ly, h=self.finger_h)

        return px.header_string(pw=1)

    def _generate_exec(self):
        # We prepare the SPICE execution
        return ".PRINT DC i(vdep)\n.DC vdep {0} {1} {2}\n".format(self.v_start, self.v_end, self.v_steps)

    def _send_command(self):
        print(self.spice_input)

        raw_results = solve_circuit(spice_file_contents=self.spice_input, postprocess_input=self.spice_preprocessor)

        return raw_results

    def _parse_output(self):
        results = parse_output(self.raw_results)

        self.V, self.I = results['dep#branch']


class SPICESolver(object):

    def __init__(self, solarcell: SolarCell, illumination: np.ndarray, metal_contact,
                 rw, cw, v_start, v_end, v_steps, Lx, Ly, h, spice_preprocessor=None):

        self.solarcell = solarcell
        self.metal_contact = metal_contact
        self.rw = rw
        self.cw = cw
        if illumination is None:
            illumination = np.ones_like(metal_contact, dtype=np.float)
        self.illumination = illumination
        self.spectrum = load_astm("AM1.5g")
        self.lx = Lx
        self.ly = Ly
        self.finger_h = h
        self.v_start = v_start
        self.v_end = v_end
        self.v_steps = v_steps
        self.r_node_num = 0
        self.c_node_num = 0
        self.V = None
        self.I = None
        self.v_junc = None
        self.steps = int(np.floor((self.v_end - self.v_start) / self.v_steps) + 1)

        # TODO temporarily add gn here
        self.gn = self._find_gn()

        self.spice_preprocessor = spice_preprocessor

        header = self._generate_header()
        nodes = self._genenerate_network()
        exec = self._generate_exec()
        spice_footer = ".end"

        self.spice_input = header + nodes + exec + spice_footer

        self.raw_results = self._send_command()

        self._parse_output()

        self._renormalize_output()

    def _find_gn(self):
        """
        find an appropriate value of gn

        :return:
        """

        coord_set = iterate_sub_image(self.metal_contact, self.rw, self.cw)

        r_pixels, c_pixels, _ = coord_set.shape

        new_illumination = resize_illumination(self.illumination, self.metal_contact, coord_set, 0)

        sample_isc = 340

        isc = np.max(new_illumination) * sample_isc * self.lx * self.ly

        return 1 / isc * 100

    def _generate_header(self):

        # TODO: this is a patch. It should be a representative pixel in illumination profile
        self.solarcell.set_input_spectrum(load_astm("AM1.5g"))

        px = PixelProcessor(self.solarcell, lx=self.lx, ly=self.ly, h=self.finger_h, gn=self.gn)

        return px.header_string(pw=self.rw)

    def _genenerate_network(self):

        # All Resistanc related information is set here.

        spice_body = """"""

        coord_set = iterate_sub_image(self.metal_contact, self.rw, self.cw)

        r_pixels, c_pixels, _ = coord_set.shape

        new_illumination = resize_illumination(self.illumination, self.metal_contact, coord_set, 0)

        assert new_illumination.shape == (r_pixels, c_pixels)

        self.r_node_num = r_pixels
        self.c_node_num = r_pixels

        # TODO wrong illumination value here, should fix it

        # We create the solar cell units and the series resistances at each node
        for c_index in range(c_pixels):
            for r_index in range(r_pixels):
                illumination_value = new_illumination[r_index, c_index]

                sub_image = self.metal_contact[coord_set[r_index, c_index, 0]:coord_set[r_index, c_index, 1],
                            coord_set[r_index, c_index, 2]:coord_set[r_index, c_index, 3]]

                # set concentration
                self.solarcell.set_input_spectrum(illumination_value * self.spectrum)

                px = PixelProcessor(self.solarcell, self.lx, self.ly, h=self.finger_h, gn=self.gn)

                spice_body += px.node_string(c_index, r_index,
                                             sub_image=sub_image, lx=self.lx, ly=self.ly)

        return spice_body

    def _generate_exec(self):

        # We prepare the SPICE execution
        return ".PRINT DC i(vdep)\n.DC vdep {0} {1} {2}\n".format(self.v_start, self.v_end, self.v_steps)

    def _send_command(self):

        raw_results = solve_circuit(spice_file_contents=self.spice_input,
                                    postprocess_input=self.spice_preprocessor.process_spice_input)

        return raw_results

    def _parse_output(self):

        results = parse_output(self.raw_results)

        self.V, self.I = results['dep#branch']

        V_junc = np.empty((self.r_node_num, self.c_node_num, self.steps))

        for xx in np.arange(self.c_node_num):
            for yy in np.arange(self.r_node_num):
                key_name = '(t_0_{:03d}_{:03d})'.format(xx, yy)
                if key_name not in results.keys():
                    key_name = self.spice_preprocessor.find_root(key_name[1:-1])
                    key_name = "(" + key_name + ")"
                try:
                    tempV, tempV2 = results[key_name]
                    assert tempV2.size == V_junc[yy, xx, :].size
                    V_junc[yy, xx, :] = tempV2
                except KeyError:
                    print("Key error when parsing output (keyname:{})".format(key_name))
                    V_junc[yy, xx, :] = 0

        self.v_junc = V_junc

    def _renormalize_output(self):

        # self.v_junc=self.v_junc*gn
        self.I = self.I / self.gn

    def get_end_voltage_map(self):

        return self.v_junc[:, :, -1]
