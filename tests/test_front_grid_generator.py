import unittest
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib as mpl

from pypvcircuit.util import add_triang_busbar, CircleGenGrid, HighResTriangGrid

from tests.helper import get_quater_image, draw_merged_contact_images

from pypvcircuit.meshing import get_merged_r_image

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
        plt.subplots_adjust(hspace=0.3)
        for i, fn in enumerate([5, 10, 15, 50]):
            hg = HighResTriangGrid(finger_n=fn)
            ax[i // 2, i % 2].imshow(hg.metal_image)
            ax[i // 2, i % 2].set_axis_off()
            ax[i // 2, i % 2].set_title("{} fingers".format(fn), fontsize=8)

        # fig.tight_layout()
        fig.savefig(os.path.join(this_path, 'test_output_data', "triang_grid.png"), dpi=600)
        fig.savefig(os.path.join(this_path, 'test_output_data', "triang_grid.pdf"))

    def test_draw_merged_image(self):

        downsample_set = [10, 20, 50, 100]

        fingers_set = [5, 10, 15, 50]

        mpl.rc('font', size=2)  # Change font.size
        mpl.rc('xtick', labelsize=2)  # change xtick.labelsize
        mpl.rc('ytick', labelsize=2)  # change ytick.labelsize

        fig, ax = plt.subplots(nrows=len(downsample_set), ncols=len(fingers_set),
                               figsize=(4.5, 4.5))

        for cc, ts in enumerate(fingers_set):
            mg = HighResTriangGrid(finger_n=int(ts))

            contacts_mask = mg.metal_image

            contacts_mask = get_quater_image(contacts_mask)

            for rr, ds in enumerate(downsample_set):
                merged_image = get_merged_r_image(contacts_mask, rw=ds, cw=ds)

                ax[rr, cc].imshow(merged_image)
                ax[rr, cc].set_axis_off()
                ax[rr, cc].grid()

        # fig.tight_layout()
        fig.savefig(os.path.join(this_path, "test_output_data", "merged_r_image.png"), dpi=300)
        fig.show()


if __name__ == '__main__':
    unittest.main()
