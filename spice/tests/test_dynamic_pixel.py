import unittest
from ..dynamic_pixel import iterate_sub_image, get_pixel_r, \
    generate_network, get_merged_r_image, resize_illumination
from skimage.io import imread, imsave
import numpy as np
import matplotlib.pyplot as plt
import os


class MyTestCase(unittest.TestCase):

    def setUp(self):

        data_path = os.path.abspath(os.path.dirname(__file__))

        self.contact_mask = imread(os.path.join('masks_sq.png'))

    def test_merged_image(self):
        contactsMask = self.contact_mask

        agg_image = get_merged_r_image(contactsMask, 5, 5)

        plt.imshow(agg_image)

        plt.show()

    def test_merge_pixel(self):
        small_tile = np.ones((5, 5), dtype=np.float)

        agg_rx, agg_ry, m_c = get_pixel_r(image=small_tile, r_x=1, r_y=1,
                                          threshold=50)

        self.assertEqual(agg_rx, np.inf)
        self.assertEqual(agg_ry, np.inf)
        self.assertEqual(m_c, 0)

    def test_network_bus_node(self):
        spicebody = generate_network(image=self.contact_mask[0:5, 0:5],
                                     rw=5, cw=5,
                                     illumination=None,
                                     metal_threshold=50,
                                     isc=np.array([1, 1, 1]),
                                     RsTop=np.array([1, 1, 1]),
                                     RsBot=np.array([1, 1, 1]),
                                     Rshunt=np.array([1, 1, 1]),
                                     Rseries=np.array([1, 1, 1]),
                                     Rcontact=10,
                                     Rline=10,
                                     Lx=10e-6, Ly=10e-6, gn=1)

        print(spicebody)

    def test_network_normal_node(self):
        spicebody = generate_network(image=np.zeros((5, 5), dtype=np.int),
                                     rw=5, cw=5,
                                     illumination=None,
                                     metal_threshold=50,
                                     isc=np.array([1, 1, 1]),
                                     RsTop=np.array([1, 1, 1]),
                                     RsBot=np.array([1, 1, 1]),
                                     Rshunt=np.array([1, 1, 1]),
                                     Rseries=np.array([1, 1, 1]),
                                     Rcontact=10,
                                     Rline=10,
                                     Lx=10e-6, Ly=10e-6, gn=1)

        print(spicebody)

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
                    get_pixel_r(sub_image, r_x=1, r_y=1, threshold=0)

                total_metal_coverage += metal_coverage * float(sub_image.size)

        total_metal_coverage = total_metal_coverage / float(mask_image.size)

        return total_metal_coverage

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
