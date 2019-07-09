import unittest
from pypvcell.solarcell import SQCell, MJCell

from pypvcircuit.spice_module_solver import SingleModuleStringSolver
from pypvcell.illumination import load_astm
import pypvcell.fom as fom

import matplotlib.pyplot as plt


class MyTestCase(unittest.TestCase):
    def test_module_string_netlist(self):
        self.gaas_1j = SQCell(1.42, 300, 1)
        self.ingap_1j = SQCell(1.87, 300, 1)
        self.ge_1j = SQCell(0.7, 300, 1)

        mj_cell = MJCell([self.ingap_1j, self.gaas_1j])

        sm = SingleModuleStringSolver(solarcell=mj_cell, illumination=500,
                                      v_start=-2, v_end=45, v_steps=0.01, l_r=1e-3, l_c=1e-3,
                                      cell_number=15, spice_preprocessor=None)

        # print(sm._generate_network())

        sm._solve_circuit()

        plt.plot(sm.V, sm.I)

        print(fom.voc(sm.V, sm.I))
        print(fom.isc(sm.V, sm.I))

        plt.show()

    def test_1j_module_string(self):
        self.gaas_1j = SQCell(1.42, 300, 1)
        self.ingap_1j = SQCell(1.87, 300, 1)
        self.ge_1j = SQCell(0.7, 300, 1)

        mj_cell = MJCell([self.ingap_1j])

        sm = SingleModuleStringSolver(solarcell=mj_cell, illumination=1,
                                      v_start=0, v_end=16, v_steps=0.01, l_r=1e-3, l_c=1e-3,
                                      cell_number=8, spice_preprocessor=None)

        # print(sm._generate_network())

        sm._solve_circuit()

        plt.plot(sm.V, sm.I)

        print(fom.voc(sm.V, sm.I))
        print(fom.isc(sm.V, sm.I))

        plt.show()


if __name__ == '__main__':
    unittest.main()
