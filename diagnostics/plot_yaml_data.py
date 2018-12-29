import yaml
import matplotlib.pyplot as plt

from tests.exp_vary_pw import plot_time_ax, plot_fill_factor, plot_isc, plot_voc

data_path = "/Users/kanhua/Dropbox/Programming/solar-cell-circuit/tests/test_output_data/{}_record.yaml"

test_set = ['highres_5', 'highres_10', 'highres_15']

fig, ax = plt.subplots(2, 2)

for ts in test_set:
    fp = open(data_path.format(ts), 'r')

    data = yaml.load(fp)

    plot_time_ax(ax[0, 0], data['pw'], data['time_elpased'])

    plot_fill_factor(ax[1, 0], data['pw'], data['ff'])
    plot_isc(ax[0, 1], data['pw'], data['isc'])
    plot_voc(ax[1, 1], data['pw'], data['voc'])

fig.savefig("/Users/kanhua/Dropbox/Programming/solar-cell-circuit/tests/test_output_data/out.png", dpi=300)
