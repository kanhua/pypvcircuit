import unittest
import math
import os

import numpy as np

import matplotlib.pyplot as plt

from spice.spice_solver import AdaptiveMeshSolver

from spice.parse_spice_input import NodeReducer
from spice.util import default_mask

from pypvcell.illumination import load_astm
from pypvcell.fom import isc, ff

from .helper import get_quater_image, load_common_setting


class AdaptiveMeshSolverTestCase(unittest.TestCase):

    def setUp(self):
        load_common_setting(self)

        self.vfin = 1.1

    def test_adaptive_solve_highest_resolution(self):
        pw = 1

        metal_mask = get_quater_image(self.default_contactsMask)
        illumination_mask = np.ones_like(metal_mask)

        nd = NodeReducer()

        self.gaas_1j.set_input_spectrum(load_astm("AM1.5g"))

        adp_solver = AdaptiveMeshSolver(solarcell=self.gaas_1j, illumination=illumination_mask,
                                        metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=self.vfin,
                                        v_steps=self.step,
                                        l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

        plt.pcolor(adp_solver.mg.ci(), adp_solver.mg.ri(), adp_solver.v_junc[:, :, -1])
        plt.show()

    def test_adaptive_solve_more_grids(self):
        pw = 5

        metal_mask = get_quater_image(self.default_contactsMask)
        illumination_mask = np.ones_like(metal_mask)

        nd = NodeReducer()

        self.gaas_1j.set_input_spectrum(load_astm("AM1.5g"))

        adp_solver = AdaptiveMeshSolver(solarcell=self.gaas_1j, illumination=illumination_mask,
                                        metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=self.vfin,
                                        v_steps=self.step,
                                        l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

        middle_r = math.ceil(adp_solver.v_junc.shape[0] / 2)

        iv_fig, iv_ax = plt.subplots(nrows=1, ncols=1)
        iv_ax.plot(adp_solver.V, adp_solver.I)

        fig, ax = plt.subplots(nrows=2, ncols=2)
        ax[0, 0].pcolor(metal_mask)
        ax[0, 0].vlines(adp_solver.mg.ci(), ymin=0, ymax=metal_mask.shape[0] - 1, colors='red', linewidths=1)

        ax[1, 0].pcolor(adp_solver.mg.ci(), adp_solver.mg.ri(), adp_solver.v_junc[:, :, -1])

        adp_solver.resolve(voltage_threshold=0)
        ax[0, 1].pcolor(metal_mask)
        ax[0, 1].vlines(adp_solver.mg.ci(), ymin=0, ymax=metal_mask.shape[0] - 1, colors='red', linewidths=1)

        ax[1, 1].pcolor(adp_solver.mg.ci(), adp_solver.mg.ri(), adp_solver.v_junc[:, :, -1])

        iv_ax.plot(adp_solver.V, adp_solver.I)

        fig.savefig(os.path.join(self.output_data_path, "mesh_on_more_grids.png"), dpi=300)
        iv_fig.savefig(os.path.join(self.output_data_path, "mesh_on_more_grids_iv.png"), dpi=300)

    def test_adaptive_solve_less_grids(self):
        pw = 10
        self.vfin = 1.3

        original_mask_image = default_mask(self.default_contactsMask.shape, finger_n=3)

        metal_mask = get_quater_image(original_mask_image)

        illumination_mask = np.ones_like(metal_mask)

        nd = NodeReducer()

        self.gaas_1j.set_input_spectrum(load_astm("AM1.5g"))

        adp_solver = AdaptiveMeshSolver(solarcell=self.gaas_1j, illumination=illumination_mask,
                                        metal_contact=metal_mask, rw=pw, cw=pw, v_start=self.vini, v_end=self.vfin,
                                        v_steps=self.step,
                                        l_r=self.lr, l_c=self.lc, h=self.h, spice_preprocessor=nd)

        iv_fig, iv_ax = plt.subplots(nrows=1, ncols=1)
        iv_ax.plot(adp_solver.V, adp_solver.I)

        fig, ax = plt.subplots(nrows=2, ncols=3)
        ax[0, 0].pcolor(metal_mask)
        ax[0, 0].vlines(adp_solver.mg.ci(), ymin=0, ymax=metal_mask.shape[0] - 1, colors='red', linewidths=1)

        ax[1, 0].pcolor(adp_solver.mg.ci(), adp_solver.mg.ri(), adp_solver.v_junc[:, :, -1])

        adp_solver.resolve(voltage_threshold=0.01)
        ax[0, 1].pcolor(metal_mask)
        ax[0, 1].vlines(adp_solver.mg.ci(), ymin=0, ymax=metal_mask.shape[0] - 1, colors='red', linewidths=1)

        ax[1, 1].pcolor(adp_solver.mg.ci(), adp_solver.mg.ri(), adp_solver.v_junc[:, :, -1])

        iv_ax.plot(adp_solver.V, adp_solver.I)

        adp_solver.resolve(voltage_threshold=0.01)
        ax[0, 2].pcolor(metal_mask)
        ax[0, 2].vlines(adp_solver.mg.ci(), ymin=0, ymax=metal_mask.shape[0] - 1, colors='red', linewidths=1)

        ax[1, 2].pcolor(adp_solver.mg.ci(), adp_solver.mg.ri(), adp_solver.v_junc[:, :, -1])

        iv_ax.plot(adp_solver.V, adp_solver.I)

        fig.savefig(os.path.join(self.output_data_path, "mesh_on_less_grids.png"), dpi=300)
        iv_fig.savefig(os.path.join(self.output_data_path, "mesh_on_less_grids_iv.png"), dpi=300)


if __name__ == '__main__':
    unittest.main()
