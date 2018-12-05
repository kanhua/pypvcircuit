import unittest
from spice.meshing import iterate_sub_image, get_merged_r_image, resize_illumination
from spice.pixel_processor import get_pixel_r
from skimage.io import imread, imsave
import numpy as np
import matplotlib.pyplot as plt
import os


class MyTestCase(unittest.TestCase):

    def setUp(self):

        self.data_path = os.path.abspath(os.path.dirname(__file__))

        self.contact_mask = imread(os.path.join('masks_sq.png'),as_grey=True)

    def test_merged_image(self):
        contactsMask = self.contact_mask

        agg_image = get_merged_r_image(contactsMask, 5, 5)

        fig, axes = plt.subplots(nrows=1, ncols=2)
        self.draw_grids_on_image(axes[0], self.contact_mask, rw=5, cw=5)

        axes[1].imshow(agg_image)

        fig.tight_layout()
        plt.savefig(os.path.join(self.data_path,"merged_image_demo.png"),dpi=300)

        plt.show()

    def test_draw_image(self):

        fig,ax=plt.subplots(ncols=1,nrows=1)
        self.draw_grids_on_image(ax,self.contact_mask, rw=5, cw=5)
        plt.show()

    def test_merge_pixel(self):
        small_tile = np.ones((5, 5), dtype=np.float)

        agg_rx, agg_ry, m_c = get_pixel_r(image=small_tile, r_row=1, r_col=1,
                                          threshold=50)

        self.assertEqual(agg_rx, np.inf)
        self.assertEqual(agg_ry, np.inf)
        self.assertEqual(m_c, 0)

    def test_metal_coverage(self):
        """
        Test if the ratio of metal coverage is constant before and after down-sampling
        :return:
        """

        mask_image = imread(os.path.join("./masks_sq.png"), as_gray=True)

        # eliminate the effects of shading
        mask_image[mask_image > 1] = 255

        imsave(os.path.join("./masks_sq_no_shades.png"), mask_image)

        metal_covered = (mask_image > 0)

        # portion of metal coverage of original image
        original_coverage = metal_covered.sum() / metal_covered.size

        # Calculate the coverage of down-samapled image

        widths = [2, 3, 5, 20]
        for pw in widths:
            total_metal_coverage = self.get_downsampled_metal_coverage(mask_image, rw=pw, cw=pw)
            self.assertAlmostEqual(original_coverage, total_metal_coverage, places=5)

    def get_downsampled_metal_coverage(self, mask_image, rw, cw):

        coord_set = iterate_sub_image(mask_image, rw=rw, cw=cw)
        r_pixels, c_pixels, _ = coord_set.shape
        total_metal_coverage = 0.0

        for c_index in range(c_pixels):
            for r_index in range(r_pixels):
                sub_image = mask_image[coord_set[r_index, c_index, 0]:coord_set[r_index, c_index, 1],
                            coord_set[r_index, c_index, 2]:coord_set[r_index, c_index, 3]]

                meta_r_x, metal_r_y, metal_coverage = \
                    get_pixel_r(sub_image, r_row=1, r_col=1, threshold=0)

                total_metal_coverage += metal_coverage * float(sub_image.size)

        total_metal_coverage = total_metal_coverage / float(mask_image.size)

        return total_metal_coverage

    def draw_grids_on_image(self, ax, mask_image, rw, cw):

        coord_set = iterate_sub_image(mask_image, rw=rw, cw=cw)
        r_pixels, c_pixels, _ = coord_set.shape

        ax.imshow(mask_image)
        ax.hlines(coord_set[1:, 0, 0], xmin=0, xmax=mask_image.shape[1] - 1,
                  colors='red', linewidths=1,alpha=0.5)
        ax.vlines(coord_set[1:, 0, 0], ymin=0, ymax=mask_image.shape[0] - 1,
                  colors='red', linewidths=1,alpha=0.5)

    def test_resize_illumination(self):

        illumination = np.ones((10, 10))
        contact_mask = np.ones((10, 10))
        contact_mask[2, 2] = 0
        contact_mask[3, 3] = 0

        coord_set = iterate_sub_image(contact_mask, 2, 2)

        rill = resize_illumination(illumination, contact_mask, coord_set)

        self.assertEqual(np.sum(illumination) - 2, np.sum(rill))


if __name__ == '__main__':
    unittest.main()
