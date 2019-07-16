import unittest
from pypvcell.solarcell import SQCell, MJCell

from pypvcircuit.spice_module_solver import SingleModuleStringSolver, MultiStringModuleSolver
from pypvcell.illumination import load_astm
import pypvcell.fom as fom

import matplotlib.pyplot as plt
import numpy as np

from pypvcircuit.parse_spice_input import NodeReducer


class MyTestCase(unittest.TestCase):
    def test_module_string_netlist(self):
        self.gaas_1j = SQCell(1.42, 300, 1)
        self.ingap_1j = SQCell(1.87, 300, 1)
        self.ge_1j = SQCell(0.7, 300, 1)

        mj_cell = MJCell([self.ingap_1j, self.gaas_1j])

        sm = SingleModuleStringSolver(solarcell=mj_cell, illumination=500,
                                      v_start=-2, v_end=80, v_steps=0.1, l_r=1e-3, l_c=1e-3,
                                      cell_number=25, spice_preprocessor=None)

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

    def test_sj_multi_string_module(self):
        self.gaas_1j = SQCell(1.42, 300, 1)
        self.ingap_1j = SQCell(1.87, 300, 1)
        self.ge_1j = SQCell(0.7, 300, 1)

        mj_cell = MJCell([self.ingap_1j])

        nd = NodeReducer()
        sm = MultiStringModuleSolver(solarcell=mj_cell, illumination=1,
                                     v_start=0, v_end=9, v_steps=0.01, l_r=1e-3, l_c=1e-3,
                                     cell_number=5, string_number=5, spice_preprocessor=nd)

        # print(sm._generate_network())

        sm._solve_circuit()

        plt.plot(sm.V, sm.I)

        print(fom.voc(sm.V, sm.I))
        print(fom.isc(sm.V, sm.I))

        plt.show()

    def test_mj_multi_string_module(self):
        self.gaas_1j = SQCell(1.42, 300, 1)
        self.ingap_1j = SQCell(1.87, 300, 1)
        self.ge_1j = SQCell(0.7, 300, 1)

        mj_cell = MJCell([self.ingap_1j, self.gaas_1j, self.ge_1j])

        nd = NodeReducer()
        sm = MultiStringModuleSolver(solarcell=mj_cell, illumination=500,
                                     v_start=0, v_end=16, v_steps=0.01, l_r=1e-3, l_c=1e-3,
                                     cell_number=5, string_number=5, spice_preprocessor=nd)

        print(sm._generate_network())

        sm._solve_circuit()

        plt.plot(sm.V, sm.I)

        print(fom.voc(sm.V, sm.I))
        print(fom.isc(sm.V, sm.I))

        plt.show()

    def test_several_cases(self):
        self.gaas_1j = SQCell(1.42, 300, 1)
        self.ingap_1j = SQCell(1.87, 300, 1)
        self.ge_1j = SQCell(0.7, 300, 1)

        mj_cell = MJCell([self.ingap_1j, self.gaas_1j, self.ge_1j])

        nd = NodeReducer()
        for i in range(2, 45):
            sm = MultiStringModuleSolver(solarcell=mj_cell, illumination=500,
                                         v_start=0, v_end=3.5 * i, v_steps=0.01, l_r=1e-3, l_c=1e-3,
                                         cell_number=i, string_number=i, isc_stdev=0.1, spice_preprocessor=None)

            # print(sm._generate_network())

            sm._solve_circuit()
            print(fom.voc(sm.V, sm.I))
            print(fom.isc(sm.V, sm.I))

            plt.plot(sm.V, sm.I)

        plt.show()

    def test_different_variation(self):

        self.gaas_1j = SQCell(1.42, 300, 1)
        self.ingap_1j = SQCell(1.87, 300, 1)
        self.ge_1j = SQCell(0.7, 300, 1)

        mj_cell = MJCell([self.ingap_1j, self.gaas_1j, self.ge_1j])

        nd = NodeReducer()

        test_stdev = np.linspace(0, 0.2, 10)
        trial = 10
        pm_store = np.empty((test_stdev.shape[0], trial))

        for std_index, stdev in enumerate(test_stdev):

            for tt in range(trial):
                sm = MultiStringModuleSolver(solarcell=mj_cell, illumination=500,
                                             v_start=0, v_end=3.5 * 5, v_steps=0.01, l_r=1e-3, l_c=1e-3,
                                             cell_number=5, string_number=5, isc_stdev=stdev, spice_preprocessor=None)

                # print(sm._generate_network())

                sm._solve_circuit()
                print(fom.voc(sm.V, sm.I))
                print(fom.isc(sm.V, sm.I))
                max_p = fom.max_power(sm.V, sm.I)

                pm_store[std_index, tt] = max_p

        print(pm_store)
        plt.plot(test_stdev, pm_store.mean(axis=1))
        plt.show()

    def test_maxp_versus_cell_num(self):

        self.gaas_1j = SQCell(1.42, 300, 1)
        self.ingap_1j = SQCell(1.87, 300, 1)
        self.ge_1j = SQCell(0.7, 300, 1)

        mj_cell = MJCell([self.ingap_1j, self.gaas_1j, self.ge_1j])

        nd = NodeReducer()

        stdev = 0.1

        cell_num_array = np.array([2, 3, 4, 5, 6, 7, 8, 9])
        trial = 10
        pm_store = np.empty((cell_num_array.shape[0], trial))
        isc_store = np.empty((cell_num_array.shape[0], trial))

        for std_index, cell_num in enumerate(cell_num_array):

            for tt in range(trial):
                sm = MultiStringModuleSolver(solarcell=mj_cell, illumination=500,
                                             v_start=0, v_end=3.5 * cell_num, v_steps=0.01, l_r=1e-3, l_c=1e-3,
                                             cell_number=cell_num, string_number=cell_num, isc_stdev=stdev,
                                             spice_preprocessor=None)

                # print(sm._generate_network())

                sm._solve_circuit()
                print(fom.voc(sm.V, sm.I))
                calc_isc = fom.isc(sm.V, sm.I)
                max_p = fom.max_power(sm.V, sm.I) / (cell_num ** 2)

                pm_store[std_index, tt] = max_p
                isc_store[std_index, tt] = calc_isc

        print(pm_store)
        plt.plot(cell_num_array, pm_store.mean(axis=1))
        plt.plot(cell_num_array, pm_store.max(axis=1))
        plt.plot(cell_num_array, pm_store.min(axis=1))
        plt.show()


if __name__ == '__main__':
    unittest.main()
