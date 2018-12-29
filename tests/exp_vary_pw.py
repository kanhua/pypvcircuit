import unittest
import timeit
import os
import numpy as np
import matplotlib.pyplot as plt
import typing
from skimage.io import imread, imsave

from pypvcell.solarcell import SQCell, MJCell
from pypvcell.illumination import load_astm
from pypvcell.fom import isc, ff, voc

from tests.helper import draw_contact_and_voltage_map, draw_merged_contact_images, \
    get_quater_image, contact_ratio, draw_illumination_3d

from pypvcircuit.parse_spice_input import NodeReducer
from pypvcircuit.spice_solver import SPICESolver, SPICESolver3D
from pypvcircuit.util import make_3d_illumination, gen_profile, HighResGrid, MetalGrid

import yaml


class PWExp(object):

    def __init__(self, illumination_mask, contacts_mask_obj: MetalGrid,
                 vini, vfin, vstep, test_pixel_width=[1, 2, 5, 10], file_prefix=""):

        self.illumination_mask = illumination_mask
        self.contacts_mask = contacts_mask_obj.metal_image
        self.l_r = contacts_mask_obj.lr
        self.l_c = contacts_mask_obj.lc

        file_path = os.path.abspath(os.path.dirname(__file__))

        self.output_data_path = os.path.join(file_path, 'test_output_data')

        self.vini = vini
        self.vfin = vfin
        self.vstep = vstep

        self.h = 2.2e-6

        self.test_pixel_width = test_pixel_width
        self.ffs = []
        self.iscs = []
        self.vocs = []
        self.elapsed_times = []

        self.file_prefix = file_prefix

    def vary_pixel_width(self, input_solar_cells: SQCell):

        l_r = self.l_r
        l_c = self.l_c

        imsave(os.path.join(self.output_data_path, "{}_ill1.png".format(self.file_prefix)), self.illumination_mask)
        imsave(os.path.join(self.output_data_path, "{}_contact1.png".format(self.file_prefix)), self.contacts_mask)

        draw_merged_contact_images(self.output_data_path, self.test_pixel_width, self.file_prefix, self.contacts_mask)

        result_vi = None

        print("original image shape:{},{}".format(*self.contacts_mask.shape))
        print("illumination total {}:".format(self.illumination_mask.sum()))

        plt.figure()

        for pw in self.test_pixel_width:

            # TODO time profiler can be added into SPICESolver
            start_time = timeit.default_timer()
            nd = NodeReducer()

            sps = SPICESolver(solarcell=input_solar_cells, illumination=self.illumination_mask,
                              metal_contact=self.contacts_mask, rw=pw, cw=pw, v_start=self.vini, v_end=self.vfin,
                              v_steps=self.vstep,
                              l_r=l_r, l_c=l_c, h=self.h, spice_preprocessor=nd)

            end_time = timeit.default_timer()

            np.save(os.path.join(self.output_data_path, "{}_vmap_{}.npy").format(self.file_prefix, pw),
                    sps.get_end_voltage_map())

            if result_vi is None:
                result_vi = np.stack((sps.V, sps.I))
            else:
                result_vi = np.vstack((result_vi, sps.V, sps.I))

            plt.plot(sps.V, sps.I, label="pw: {}".format(pw))
            fill_factor = ff(sps.V, sps.I)
            calculated_isc = isc(sps.V, sps.I)
            cell_voc = voc(sps.V, sps.I)

            e_time = end_time - start_time
            print("Jsc: {:2f} A/m^2".format(calculated_isc))
            print("fill factor of pw {}: {}".format(pw, fill_factor))
            print("Voc of pw {}: {:.2f}".format(pw, cell_voc))
            print("time elapsed: {:.2f} sec.".format(e_time))
            self.elapsed_times.append(e_time)
            self.vocs.append(float(cell_voc))
            self.iscs.append(float(calculated_isc))
            self.ffs.append(float(fill_factor))

        draw_contact_and_voltage_map(self.output_data_path, self.test_pixel_width, self.file_prefix, self.contacts_mask)

        np.savetxt(os.path.join(self.output_data_path, "{}_iv.csv".format(self.file_prefix)), result_vi.T,
                   delimiter=',')

        plt.savefig(os.path.join(self.output_data_path, "{}_1jfig.png".format(self.file_prefix)))

        plt.close()

        self.dump_data()

    def plot_time(self):

        plt.figure()

        fig, ax = plt.subplots()

        plot_time_ax(ax, self.test_pixel_width, self.elapsed_times)

        plt.savefig(os.path.join(self.output_data_path, "{}_elapsed_time.png".format(self.file_prefix)), dpi=300)

    def dump_data(self):

        yfp = open(os.path.join(self.output_data_path, "{}_record.yaml").format(self.file_prefix), 'w')
        yaml.dump({'pw': self.test_pixel_width,
                   'time_elpased': self.elapsed_times,
                   'ff': self.ffs,
                   'voc': self.vocs,
                   'isc': self.iscs}, yfp)
        yfp.close()


def plot_time_ax(ax, pixel_width, elapsed_times):
    ax.plot(pixel_width, elapsed_times, 'o-')
    ax.set_xlabel("down-sampling ratio")
    ax.set_ylabel("execution time (sec)")
