import yaml
import numpy as np
import matplotlib.pyplot as plt
from os.path import join
import os

from pypvcell.fom import ff, isc

from pypvcircuit.util import HighResGrid, HighResTriangGrid
from tests.exp_vary_pw import plot_time_ax, plot_fill_factor, plot_isc, plot_voc
from tests.helper import draw_contact_and_voltage_map, get_quater_image

import matplotlib as mpl

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("setfile", help="A yaml file that does the basic setting")
args = parser.parse_args()
fp = open(args.setfile, 'r')
print(args.setfile)

setting = yaml.load(fp)
fp.close()

data_path = os.path.join(setting['data_path'], "{}_record.yaml")
iv_data_path = os.path.join(setting['iv_data_path'], "{}_iv.csv")
output_data_path = setting['output_data_path']

mpl.rc('font', size=8)  # Change font.size
mpl.rc('xtick', labelsize=8)  # change xtick.labelsize
mpl.rc('ytick', labelsize=8)  # change ytick.labelsize


def plot_iv(ax, iv_file, pw):
    iv = np.loadtxt(iv_file, delimiter=',')

    for i in range(0, iv.shape[1], 2):
        volt = iv[:, i]
        curr = iv[:, i + 1] * 1e3
        isc_val = isc(volt, curr)
        ff_val = ff(volt, curr)

        ax.plot(volt, curr, label="{} x".format(pw[int(i / 2)], isc_val, ff_val), alpha=0.5)
        ax.set_ylim(ymax=0)
        ax.set_ylim(ymin=curr[0] * 1.5)

        ax.set_xlabel("voltage (V)")
        ax.set_ylabel("current (mA)")

    ax.legend()
    ax.grid()


def draw_voltage_map(output_data_path, test_pws, axes_to_draw, file_prefix: str):
    for i, pw in enumerate(test_pws):
        voltage_map = np.load(os.path.join(output_data_path, "{}_vmap_{}.npy").format(file_prefix, pw))
        # axes_to_draw[i].set_axis_off()
        axes_to_draw[i].set_title("{} x".format(test_pws[i]))
        axes_to_draw[i].imshow(voltage_map)


test_set = setting['fingers_set']

fig, ax = plt.subplots(2, 2, figsize=(2.5 * 2, 2.5 * 3.25 / 3.5 * 2))

for ts in test_set:
    full_filename = setting['file_prefix'] + "_{}".format(ts)
    fp = open(data_path.format(full_filename), 'r')

    data = yaml.load(fp)
    fp.close()

    # plot IV
    fig_iv, ax_iv = plt.subplots(figsize=(2.5, 2.5))

    plot_iv(ax_iv, iv_data_path.format(full_filename), data['pw'])

    fig_iv.tight_layout()
    fig_iv.savefig(os.path.join(setting['output_data_path'], "{}_iv.png".format(full_filename)),
                   dpi=300)

    # plot voltage map
    plot_time_ax(ax[0, 0], data['pw'], data['time_elpased'], ts)

    plot_fill_factor(ax[1, 0], data['pw'], data['ff'])
    plot_isc(ax[0, 1], data['pw'], data['isc'])
    plot_voc(ax[1, 1], data['pw'], data['voc'])

    mg = HighResTriangGrid(finger_n=int(ts))

    contacts_mask = mg.metal_image

    contacts_mask = get_quater_image(contacts_mask)

    draw_contact_and_voltage_map(output_data_path, data['pw'], full_filename, contacts_mask)

    voltage_map_fig, voltage_map_ax = plt.subplots(2, 2, figsize=(2.5, 2.5))
    voltage_map_ax = voltage_map_ax.ravel()
    draw_voltage_map(setting['data_path'], data['pw'], voltage_map_ax, full_filename)
    voltage_map_fig.tight_layout()
    voltage_map_fig.savefig(os.path.join(output_data_path, "{}_equiv_map_images.png".format(full_filename)), dpi=300)

fig.tight_layout()
fom_filename = "{}_fom.png".format(setting['file_prefix'])
fig.savefig(os.path.join(setting['output_data_path'], fom_filename), dpi=300)
fig.savefig(os.path.join(setting['mirror_output_data_path'], fom_filename), dpi=300)
