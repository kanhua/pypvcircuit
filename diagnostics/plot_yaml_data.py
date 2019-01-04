import yaml
import matplotlib.pyplot as plt
from os.path import join

from pypvcircuit.util import HighResGrid
from tests.exp_vary_pw import plot_time_ax, plot_fill_factor, plot_isc, plot_voc
from tests.helper import draw_contact_and_voltage_map, get_quater_image

data_path = "/Users/kanhua/Dropbox/Programming/solar-cell-circuit/tests/test_output_data/{}_record.yaml"
output_data_path = "/Users/kanhua/Dropbox/Programming/solar-cell-circuit/tests/test_output_data/"

test_set = ['highres_5', 'highres_10', 'highres_15']

fig, ax = plt.subplots(2, 2, figsize=(9, 6))

for ts in test_set:
    ab = ts.split("_")

    fp = open(data_path.format(ts), 'r')

    data = yaml.load(fp)

    plot_time_ax(ax[0, 0], data['pw'], data['time_elpased'])

    plot_fill_factor(ax[1, 0], data['pw'], data['ff'])
    plot_isc(ax[0, 1], data['pw'], data['isc'])
    plot_voc(ax[1, 1], data['pw'], data['voc'])

    mg = HighResGrid(finger_n=int(ab[1]))

    contacts_mask = mg.metal_image

    contacts_mask = get_quater_image(contacts_mask)

    draw_contact_and_voltage_map(output_data_path, data['pw'], ts, contacts_mask)

fig.tight_layout()
fig.savefig("/Users/kanhua/Dropbox/Programming/solar-cell-circuit/tests/test_output_data/highres_fom.png", dpi=300)
fig.savefig("/Users/kanhua/Dropbox/DDocuments/2018-equivalent-circuit/figs/highres_fom.png", dpi=300)
