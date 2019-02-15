import typing
import math
import numpy as np

from .meshing import iterate_sub_image, resize_illumination, \
    MeshGenerator, resize_illumination_3d
from .pixel_processor import PixelProcessor, create_header
from .spice_interface import solve_circuit
from .parse_spice_output import parse_output

from pypvcell.solarcell import SolarCell
from pypvcell.illumination import load_astm
from pypvcell.spectrum import Spectrum


def _get_steps(start_val, end_val, step):
    """

    The naive implementation
    int(np.floor((self.v_end - self.v_start) / self.v_steps) + 1)
    does not work
    For example: 12/0.05 gives 23.9999999

    :param start_val:
    :param end_val:
    :param step:
    :return:
    """

    arr = np.arange(start_val, end_val, step)

    return arr.size + 1


class SPICESolver(object):
    """
    Base class of SPICE solver. The solver is launched in the contructor (__init__()).

    """

    def __init__(self, solarcell: SolarCell, illumination: np.ndarray, metal_contact: np.ndarray,
                 rw: int, cw: int, v_start, v_end, v_steps, l_r, l_c, h, spice_preprocessor=None,
                 illumination_spectrum: typing.Optional[Spectrum] = None,
                 illumination_wavelength: typing.Optional[np.ndarray] = None,
                 illumination_unit='x'):
        """
        This function initialize the mesh and runs the network simulation.

        :param solarcell: the Pypvcell solar cell class
        :param illumination: a 2D or 3D numpy array
        :param metal_contact: a 2D numpy array that describes the metal contact
        :param rw: the downsampling ratio in row direction
        :param cw: the downsampling ration in column direction
        :param v_start: the value of starting voltage
        :param v_end:  the value of the end voltage
        :param v_steps: the voltage step
        :param l_r: the physical width of pixel in row direction (meter)
        :param l_c: the physical widht of pixel in column direction (meter)
        :param h: the height of the finger
        :param spice_preprocessor: a preprocessor for processing the netlist file before solving it. It is typically to be set to a nodereducer class, i.e. preprocessor=NodeReducer()
        :param illumination_spectrum:
        :param illumination_wavelength: a 1D wavelenght array. The size should be identical t
        :param illumination_unit: The unit of illumination matrix. It can either be 'x' (concentration) or 'W' (watt)
        """

        self.solarcell = solarcell
        self.metal_contact = metal_contact
        self.rw = rw
        self.cw = cw
        if illumination is None:
            illumination = np.ones_like(metal_contact, dtype=np.float)
        self.illumination = illumination
        self.illumination_wavelength = illumination_wavelength

        assert illumination_unit == 'x' or illumination_unit == 'W'
        self.illumination_unit = illumination_unit

        if illumination_spectrum is None:
            self.spectrum = load_astm("AM1.5g")
        else:
            self.spectrum = illumination_spectrum
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
        self.steps = _get_steps(self.v_start, self.v_end, self.v_steps)

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
        new_illumination = resize_illumination(self.illumination, self.metal_contact, coord_set)
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
        self.I = -self.I / self.gn

    def get_end_voltage_map(self):

        return self.v_junc[:, :, -1]


class SPICESolver3D(SPICESolver):

    def _check_illumination_wavelength(self):

        assert self.illumination_wavelength.size == self.illumination.shape[2]

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

        self._check_illumination_wavelength()

        spice_body = ""
        r_pixels, c_pixels, _ = coord_set.shape
        new_illumination = resize_illumination_3d(self.illumination, self.metal_contact, coord_set, 0)
        assert new_illumination.shape == (r_pixels, c_pixels, self.illumination.shape[2])

        self.r_node_num = r_pixels
        self.c_node_num = c_pixels

        # procedures: run thought all x and y pixels
        for c_index in range(c_pixels):
            for r_index in range(r_pixels):
                illumination_value = new_illumination[r_index, c_index, :]

                sub_image = self.metal_contact[coord_set[r_index, c_index, 0]:coord_set[r_index, c_index, 1],
                            coord_set[r_index, c_index, 2]:coord_set[r_index, c_index, 3]]

                # set concentration
                if self.illumination_unit == 'x':
                    sp = Spectrum(self.illumination_wavelength, illumination_value, x_unit='nm')

                    self.solarcell.set_input_spectrum(self.spectrum * sp)
                elif self.illumination_unit == 'W':
                    sp = Spectrum(self.illumination_wavelength, illumination_value, x_unit='nm',
                                  y_unit='mm**-2')
                    # TODO setting y_unit here is not very robust.
                    self.solarcell.set_input_spectrum(sp)

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
