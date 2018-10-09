import unittest
from ..dynamic_pixel import iterate_sub_image, get_pixel_r, generate_network
from skimage.io import imread
import numpy as np
import matplotlib.pyplot as plt


class MyTestCase(unittest.TestCase):

    def setUp(self):

        self.contact_mask = imread('masks_sq.png')

    def test_something(self):

        contactsMask = imread('masks_sq.png')

        sub_image_coord = iterate_sub_image(contactsMask, 5, 5)

        agg_image = np.zeros((sub_image_coord.shape[0], sub_image_coord.shape[1]))

        for i in range(sub_image_coord.shape[0]):
            for j in range(sub_image_coord.shape[1]):
                a, b, c, d = sub_image_coord[i, j, :]
                agg_image[i, j] = np.sum(contactsMask[a:b, c:d])

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

        spicebody = generate_network(image=np.zeros((5,5),dtype=np.int),
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


if __name__ == '__main__':
    unittest.main()
