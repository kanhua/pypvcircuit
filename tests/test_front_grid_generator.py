import unittest
import numpy as np
import matplotlib.pyplot as plt

from pypvcircuit.util import add_triang_busbar


class ContactProfileTest(unittest.TestCase):

    def test_triang_profile(self):
        image_shape = (1000, 1000)
        test_image = np.zeros(image_shape, dtype=np.uint8)

        test_image = add_triang_busbar(test_image, bus_width=0.05, margin_c=0.02, margin_r=0.02)

        plt.imshow(test_image)
        plt.show()


if __name__ == '__main__':
    unittest.main()
