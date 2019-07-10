import typing
import math
import numpy as np

from pypvcell.solarcell import SolarCell
from pypvcell.illumination import load_astm
from pypvcell.spectrum import Spectrum

from .parse_spice_output import parse_output
from .pixel_processor import PixelProcessor, create_header
from .spice_interface import solve_circuit
from .spice_solver import SPICESolver


class SingleModuleStringSolver(SPICESolver):

    def __init__(self, solarcell: SolarCell, illumination: float, v_start,
                 v_end, v_steps, l_r, l_c, cell_number, spice_preprocessor=None):
        self.solarcell = solarcell

        self.l_r = l_r
        self.l_c = l_c
        self.illumination = illumination

        self.v_start = v_start
        self.v_end = v_end
        self.v_steps = v_steps

        self.cell_number = cell_number

        self.V = None
        self.I = None

        self.spice_preprocessor = spice_preprocessor

        self.gn = self._find_gn()

        # self._solve_circuit()

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

    def _send_command(self):

        postprocessor = None
        if self.spice_preprocessor is not None:
            postprocessor = self.spice_preprocessor.process_spice_input

        raw_results = solve_circuit(spice_file_contents=self.spice_input,
                                    postprocess_input=postprocessor)

        return raw_results

    def _generate_header(self, temperature):

        title = "*** A SPICE simulation with python\n\n"

        options = ".OPTIONS TNOM=20 TEMP={0}\n\n".format(temperature)

        header_string = title + options

        return header_string

    def _find_gn(self):
        sample_isc = 340

        isc = self.illumination * sample_isc * self.l_c * self.l_r

        return 1 / isc / 10000

    def _generate_network(self):

        self.solarcell.set_input_spectrum(load_astm("AM1.5g") * self.illumination)

        spj = ""
        node_count = 0
        junction_count = 0
        for cn in range(self.cell_number):

            lowerBypassConnection = node_count
            for jn in range(len(self.solarcell.subcell)):
                spj += spice_junction(junction_count, node_count,
                                      self.solarcell.subcell[jn].jsc * self.l_c * self.l_r * self.gn,
                                      self.solarcell.subcell[jn].j01 * self.l_c * self.l_r * self.gn,
                                      self.solarcell.subcell[jn].j02,
                                      n1=1, n2=2, Eg=self.solarcell.subcell[jn].eg, rsh=1e14)
                junction_count += 1
                node_count += 1

                # Add the series resistance
            # spiceout = 'r{0} {1} {2} {3}\n'.format(2 * junction_count - 1, node_count+1, node_count, 1e-8)
            # node_count += 1
            # spj+=spiceout

            # Connect bypass diode.  Connections are: lowerBypassConnection & nodeCounter
            # spiceout = 'd{0} {1} {2} bypassdiode\n'.format(2 * junction_count + 1, lowerBypassConnection, node_count)
            # spj+=spiceout
            # junction_count += 1

        # add bias

        spj += "vdep " + str(junction_count) + " 0\n"

        return spj

    def _parse_output(self):
        results = parse_output(self.raw_results)

        self.V, self.I = results['dep#branch']

    def _generate_exec(self):

        # We prepare the SPICE execution
        return ".PRINT DC i(vdep)\n.DC vdep {0} {1} {2}\n".format(self.v_start, self.v_end, self.v_steps)


class MultiStringModuleSolver(SingleModuleStringSolver):

    def __init__(self, solarcell: SolarCell, illumination: float, v_start,
                 v_end, v_steps, l_r, l_c, cell_number, string_number, spice_preprocessor=None):
        self.solarcell = solarcell

        self.l_r = l_r
        self.l_c = l_c
        self.illumination = illumination

        self.v_start = v_start
        self.v_end = v_end
        self.v_steps = v_steps

        self.cell_number = cell_number
        self.string_number = string_number

        self.V = None
        self.I = None

        self.spice_preprocessor = spice_preprocessor

        self.gn = self._find_gn()

    def _generate_network(self):

        self.solarcell.set_input_spectrum(load_astm("AM1.5g") * self.illumination)

        spj = ""

        start_node_count = 0

        node_count = start_node_count
        junction_count = start_node_count

        junction_number = len(self.solarcell.subcell)

        for sn in range(self.string_number):

            for cn in range(self.cell_number):
                for jn in range(len(self.solarcell.subcell)):
                    spj += spice_junction(junction_count, node_count,
                                          self.solarcell.subcell[jn].jsc * self.l_c * self.l_r * self.gn,
                                          self.solarcell.subcell[jn].j01 * self.l_c * self.l_r * self.gn,
                                          self.solarcell.subcell[jn].j02,
                                          n1=1, n2=2, Eg=self.solarcell.subcell[jn].eg, rsh=1e14)
                    junction_count += 1
                    node_count += 1

            junction_count += 1
            node_count += 1
            # connect the nodes between strings
            resistor_str1 = ""
            resistor_str2 = ""
            if sn >= 1:
                resistor_str1 = 'r{0} {1} {2} {3}\n'.format("sn_head_{}".format(sn), start_node_count,
                                                            node_count - junction_number * self.cell_number - 1, 1e-9)
                resistor_str2 = 'r{0} {1} {2} {3}\n'.format("sn_tail_{}".format(sn),
                                                            start_node_count + junction_number * self.cell_number,
                                                            node_count - 1, 1e-9)

            spj += (resistor_str1 + resistor_str2)

        vsource = "vdep {0} {1} \n".format(junction_count - 1, start_node_count)
        spj += vsource

        return spj


def spice_junction(jc, nc, isc, j01, j02, n1, n2, Eg, rsh):
    """ Creates the string representation in SPICE of the junciton defined by the input values.

    This function was adopted from solcore5:
    solcore.spice.pv_module_solver.spice_junction

    :param jc: junction counter
    :param nc: node counter
    :param isc: Short circuit current
    :param j01: Reverse saturation current corresponding to ideality factor n1
    :param j02: Reverse saturation current corresponding to ideality factor n2
    :param n1: Ideality factor, typically = 1
    :param n2: Ideality factor, typically = 2
    :param Eg: Bandgap of the material the junction is made off
    :param rsh: Shunt resistance in the junction
    :return: A string representation of the junciton in SPICE
    """

    isource = 'i{0} {1} {2} dc {3}\n'.format(jc, nc, nc + 1, isc)
    d1 = 'd{0} {1} {2} diode{3} OFF\n'.format(2 * jc - 1, nc + 1, nc, 2 * jc - 1)
    d1deff = '.model diode{0} d(is={1},n={2},eg={3})\n'.format(2 * jc - 1, j01, n1, Eg)

    if j02 is not None:
        d2 = 'd{0} {1} {2} diode{3} OFF\n'.format(2 * jc, nc + 1, nc, 2 * jc)
        d2deff = '.model diode{0} d(is={1},n={2},eg={3})\n'.format(2 * jc, j02, n2, Eg)
    else:
        d2 = ""
        d2deff = ""

    rshunt = 'r{0} {1} {2} {3}\n'.format(2 * jc, nc + 1, nc, rsh)
    # rshunt=""
    junction = isource + d1 + d1deff + d2 + d2deff + rshunt

    return junction
