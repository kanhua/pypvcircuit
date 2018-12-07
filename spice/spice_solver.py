import typing
import math
import numpy as np
from .meshing import iterate_sub_image, resize_illumination, \
    MeshGenerator, convert_boundary_to_coordset, resize_illumination_3d
from .pixel_processor import PixelProcessor, create_header
from .spice_interface import solve_circuit
from .parse_spice_output import parse_output

from pypvcell.solarcell import SQCell, SolarCell
from pypvcell.illumination import load_astm
from pypvcell.spectrum import Spectrum


class SPICESolver(object):

    def __init__(self, solarcell: SolarCell, illumination: np.ndarray, metal_contact: np.ndarray,
                 rw: int, cw: int, v_start, v_end, v_steps, l_r, l_c, h, spice_preprocessor=None):

        self.solarcell = solarcell
        self.metal_contact = metal_contact
        self.rw = rw
        self.cw = cw
        if illumination is None:
            illumination = np.ones_like(metal_contact, dtype=np.float)
        self.illumination = illumination
        self.spectrum = load_astm("AM1.5g")
        self.l_r = l_r
        self.l_c = l_c
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

        self.spice_preprocessor = spice_preprocessor

        self.mg = MeshGenerator(image_shape=metal_contact.shape, rw=rw, cw=cw)

        # TODO temporarily add gn here
        self.gn = self._find_gn()

        self._solve_circuit()

    def _solve_circuit(self):
        # TODO add temperature as an object parameter
        header = self._generate_header(temperature=20)
        nodes = self._generate_network()
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

        isc = np.max(new_illumination) * sample_isc * self.l_r * self.l_c

        return 1 / isc * 100

    def _generate_header(self, temperature):

        return create_header(T=temperature)

    def _generate_network(self):

        coord_set = self.mg.to_coordset()

        return self._write_nodes(coord_set)

    def _write_nodes(self, coord_set):
        spice_body = ""
        r_pixels, c_pixels, _ = coord_set.shape
        new_illumination = resize_illumination(self.illumination, self.metal_contact, coord_set, 0)
        assert new_illumination.shape == (r_pixels, c_pixels)
        self.r_node_num = r_pixels
        self.c_node_num = c_pixels
        for c_index in range(c_pixels):
            for r_index in range(r_pixels):
                illumination_value = new_illumination[r_index, c_index]

                sub_image = self.metal_contact[coord_set[r_index, c_index, 0]:coord_set[r_index, c_index, 1],
                            coord_set[r_index, c_index, 2]:coord_set[r_index, c_index, 3]]

                # set concentration
                self.solarcell.set_input_spectrum(illumination_value * self.spectrum)

                px = PixelProcessor(self.solarcell, self.l_r, self.l_c, h=self.finger_h, gn=self.gn)

                spice_body += px.node_string(r_index, c_index, sub_image=sub_image)
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

        for col_idx in np.arange(self.c_node_num):
            for row_idx in np.arange(self.r_node_num):
                key_name = '(t_0_{:03d}_{:03d})'.format(row_idx, col_idx)
                if key_name not in results.keys():
                    key_name = self.spice_preprocessor.find_root(key_name[1:-1])
                    key_name = "(" + key_name + ")"
                try:
                    tempV, tempV2 = results[key_name]
                    assert tempV2.size == V_junc[row_idx, col_idx, :].size
                    V_junc[row_idx, col_idx, :] = tempV2
                except KeyError:
                    print("Key error when parsing output (keyname:{})".format(key_name))
                    V_junc[row_idx, col_idx, :] = 0

        self.v_junc = V_junc

    def _renormalize_output(self):

        # self.v_junc=self.v_junc*gn
        self.I = self.I / self.gn

    def get_end_voltage_map(self):

        return self.v_junc[:, :, -1]


class SPICESolver3D(SPICESolver):
    """

    #TODO for now we assume the wavelenghts of the reference spectrum is identical to load_astm("AM1.5g)

    """

    def _find_gn(self):
        """
        find an appropriate value of gn

        :return:
        """

        coord_set = iterate_sub_image(self.metal_contact, self.rw, self.cw)

        r_pixels, c_pixels, _ = coord_set.shape

        nz = self.illumination.shape[2]

        new_illumination = resize_illumination(self.illumination[:, :, int(nz / 2)], self.metal_contact, coord_set, 0)

        sample_isc = 340

        isc = np.max(new_illumination) * sample_isc * self.l_r * self.l_c

        return 1 / isc * 100

    def _write_nodes(self, coord_set):
        spice_body = ""
        r_pixels, c_pixels, _ = coord_set.shape
        new_illumination = resize_illumination_3d(self.illumination, self.metal_contact, coord_set, 0)
        assert new_illumination.shape == (r_pixels, c_pixels, self.illumination.shape[2])
        self.r_node_num = r_pixels
        self.c_node_num = c_pixels
        for c_index in range(c_pixels):
            for r_index in range(r_pixels):
                illumination_value = new_illumination[r_index, c_index, :]

                sub_image = self.metal_contact[coord_set[r_index, c_index, 0]:coord_set[r_index, c_index, 1],
                            coord_set[r_index, c_index, 2]:coord_set[r_index, c_index, 3]]

                # set concentration
                data = self.spectrum.get_spectrum(to_x_unit='nm')
                x_data = data[0, :]

                sp = Spectrum(x_data, illumination_value, x_unit='nm')

                self.solarcell.set_input_spectrum(self.spectrum * sp)

                px = PixelProcessor(self.solarcell, self.l_r, self.l_c, h=self.finger_h, gn=self.gn)

                spice_body += px.node_string(r_index, c_index, sub_image=sub_image)
        return spice_body


class SinglePixelSolver(SPICESolver):

    def __init__(self, solarcell: SolarCell, illumination: float, v_start,
                 v_end, v_steps, l_r, l_c, h, spice_preprocessor=None):
        self.solarcell = solarcell

        self.l_r = l_r
        self.l_c = l_c
        self.finger_h = h
        self.illumination = illumination

        self.v_start = v_start
        self.v_end = v_end
        self.v_steps = v_steps

        self.V = None
        self.I = None

        self.spice_preprocessor = spice_preprocessor

        self.gn = self._find_gn()

        self._solve_circuit()

    def _find_gn(self):
        sample_isc = 340

        isc = self.illumination * sample_isc * self.l_c * self.l_r

        return 1 / isc * 100

    def _generate_network(self):
        dummy_image = np.array([[255]])

        self.solarcell.set_input_spectrum(load_astm("AM1.5g") * self.illumination)

        px = PixelProcessor(self.solarcell, self.l_r, self.l_c, h=self.finger_h, gn=self.gn)

        return px.node_string(id_r=0, id_c=0, sub_image=dummy_image, is_boundary_r=True, is_boundary_c=True)

    def _parse_output(self):
        results = parse_output(self.raw_results)

        self.V, self.I = results['dep#branch']

    def get_end_voltage_map(self):
        raise NotImplementedError("Single pixel solver does not support voltage map")


class AdaptiveMeshSolver(SPICESolver):
    """
    This class is still in experimental phase.
    This solver inherits everything from SPICESolver,
    except that it has a resolve() method to remesh and then solve the circuit again.
    In other words, the iterative solving process is not yet implemented.
    The user has to manually write a loop and perform resolve() to get satisfactory results.


    """

    def _remesh(self, voltage_threshold=0.0):
        voltage_map = self.v_junc[:, :, -1]

        middle_r = math.ceil(voltage_map.shape[0] / 2)

        rep_voltage = voltage_map[middle_r, :]

        self.mg.refine(y=rep_voltage, delta_y=voltage_threshold, dim=1)

    def resolve(self, voltage_threshold):
        self._remesh(voltage_threshold=voltage_threshold)
        self._solve_circuit()
