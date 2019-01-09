import unittest
import numpy as np
import os
import matplotlib.pyplot as plt

from pypvcircuit.util import add_triang_busbar, CircleGenGrid, HighResTriangGrid

this_path = os.path.abspath(os.path.dirname(__file__))


class ContactProfileTest(unittest.TestCase):

    def test_triang_profile(self):
        image_shape = (1000, 1000)
        test_image = np.zeros(image_shape, dtype=np.uint8)

        test_image = add_triang_busbar(test_image, bus_width=0.05, margin_c=0.02, margin_r=0.02)

        plt.imshow(test_image)
        plt.show()

    def test_circle_profile(self):
        cr = CircleGenGrid()
        plt.imshow(cr.metal_image)
        plt.show()

    def test_draw_triang_profile(self):
        fig, ax = plt.subplots(ncols=2, nrows=2, figsize=(2.5, 2.5))
        for i, fn in enumerate([5, 10, 15, 50]):
            hg = HighResTriangGrid(finger_n=fn)
            ax[i // 2, i % 2].imshow(hg.metal_image)
            ax[i // 2, i % 2].set_axis_off()
            ax[i // 2, i % 2].set_title("{} fingers".format(fn), fontsize=8)

        # fig.tight_layout()
        fig.savefig(os.path.join(this_path, "triang_grid.png"), dpi=300)


if __name__ == '__main__':
    unittest.main()
