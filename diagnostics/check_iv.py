import numpy as np
import matplotlib.pyplot as plt

from pypvcell.fom import ff, isc

iv_file = "/Users/kanhua/Dropbox/Programming/solar-cell-circuit/tests/test_output_data/3j_ingap_iv.csv"

iv = np.loadtxt(iv_file, delimiter=',')
pw = [1, 2, 5, 10]

for i in range(0, iv.shape[1], 2):
    volt = iv[:, i]
    curr = iv[:, i + 1]
    isc_val = isc(volt, curr)
    ff_val = ff(volt, curr)

    plt.plot(volt, curr, label="PW: {} Isc: {:.2f}, FF:{:.2f}".format(pw[int(i / 2)], isc_val, ff_val))
    plt.ylim(ymax=0)
    plt.ylim(ymin=curr[0] * 1.5)

    plt.xlabel("voltage (V)")
    plt.ylabel("current (A)")

plt.legend()
plt.grid()

plt.savefig("iv_3j.png")
plt.show()
