import yaml
import numpy as np
import matplotlib.pyplot as plt
from os.path import join

from pypvcell.fom import ff, isc

from pypvcircuit.util import HighResGrid, HighResTriangGrid
from tests.exp_vary_pw import plot_time_ax, plot_fill_factor, plot_isc, plot_voc
from tests.helper import draw_contact_and_voltage_map, get_quater_image

import matplotlib as mpl

mpl.rc('font', size=8)  # Change font.size
mpl.rc('xtick', labelsize=8)  # change xtick.labelsize
mpl.rc('ytick', labelsize=8)  # change ytick.labelsize

data_path = "/Users/kanhua/Dropbox/Programming/solar-cell-circuit/tests/test_output_data/{}_record.yaml"
iv_data_path = "/Users/kanhua/Dropbox/Programming/solar-cell-circuit/tests/test_output_data/{}_iv.csv"
output_data_path = "/Users/kanhua/Dropbox/Programming/solar-cell-circuit/tests/test_output_data/"


def plot_iv(ax, iv_file, pw):
    iv = np.loadtxt(iv_file, delimiter=',')

    for i in range(0, iv.shape[1], 2):
        volt = iv[:, i]
        curr = iv[:, i + 1] * 1e6
        isc_val = isc(volt, curr)
        ff_val = ff(volt, curr)

        ax.plot(volt, curr, label="PW: {}".format(pw[int(i / 2)], isc_val, ff_val), alpha=0.5)
        ax.set_ylim(ymax=0)
        ax.set_ylim(ymin=curr[0] * 1.5)

        ax.set_xlabel("voltage (V)")
        ax.set_ylabel("current (uA)")

    ax.legend()
    ax.grid()


test_set = ['highres_triang_5mm_5', 'highres_triang_5mm_10', 'highres_triang_5mm_15']

fig, ax = plt.subplots(2, 2, figsize=(2.5 * 2, 2.5 * 3.25 / 3.5 * 2))

for ts in test_set:
    ab = ts.split("_")

    fp = open(data_path.format(ts), 'r')

    data = yaml.load(fp)
    fp.close()

    # plot IV
    fig_iv, ax_iv = plt.subplots(figsize=(2.5, 2.5 * 3.25 / 3.5))

    plot_iv(ax_iv, iv_data_path.format(ts), data['pw'])

    fig_iv.tight_layout()
    fig_iv.savefig("/Users/kanhua/Dropbox/DDocuments/2018-equivalent-circuit/figs/{}_iv.png".format(ts), dpi=300)

    # plot voltage map
    plot_time_ax(ax[0, 0], data['pw'], data['time_elpased'], ts)

    plot_fill_factor(ax[1, 0], data['pw'], data['ff'])
    plot_isc(ax[0, 1], data['pw'], data['isc'])
    plot_voc(ax[1, 1], data['pw'], data['voc'])

    mg = HighResTriangGrid(finger_n=int(ab[-1]))

    contacts_mask = mg.metal_image

    contacts_mask = get_quater_image(contacts_mask)

    draw_contact_and_voltage_map(output_data_path, data['pw'], ts, contacts_mask)

fig.tight_layout()
fig.savefig("/Users/kanhua/Dropbox/Programming/solar-cell-circuit/tests/test_output_data/highres_fom.png", dpi=300)
fig.savefig("/Users/kanhua/Dropbox/DDocuments/2018-equivalent-circuit/figs/highres_fom.png", dpi=300)
