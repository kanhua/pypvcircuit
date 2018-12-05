import unittest
import os
import numpy as np

import matplotlib.pyplot as plt

from spice.meshing import single_step_remeshing, middle_point_ceil, middle_point


def example_func_1(x):
    return 1 / np.power(x, 2)


class AdaptiveMeshTestCase(unittest.TestCase):

    def setUp(self):
        file_path = os.path.abspath(os.path.dirname(__file__))

        self.output_data_path = os.path.join(file_path, 'test_output_data')

    def test_np_insert(self):
        """
        Convince myself the np.insert() is doing what I expect

        :return:
        """

        a1 = np.array([0, 1, 4, 7])

        # insert one chunk of elements
        # if len(obj)==1, then np.insert can insert a chunk of elements
        a2 = np.insert(a1, 2, [2, 3])

        result = np.array_equal(a2, np.array([0, 1, 2, 3, 4, 7]))

        self.assertTrue(result)

        # if len(obj)>1, then np.insert can insert a chunk of elements
        # np.insert() inserts every values[i] to every a1[obj[i]]
        a3 = np.insert(a1, [2, 3], [2, 5])

        result = np.array_equal(a3, np.array([0, 1, 2, 4, 5, 7]))

        self.assertTrue(result)

    def test_func(self):
        init_x = np.arange(1, 10, dtype=np.float)
        init_y = example_func_1(init_x)

        plt.plot(init_x, init_y, '.--', alpha=0.5)

        next_x = np.copy(init_x)
        next_y = np.copy(init_y)

        # run a few iteration
        for i in range(3):
            next_x = single_step_remeshing(next_x, next_y, delta_y=0.1, interp_func=middle_point)
            next_y = example_func_1(next_x)
            plt.plot(next_x, next_y, '.--', alpha=0.5)

        plt.show()

    def test_index_mapping(self):
        init_x = np.arange(1, 10, step=3, dtype=np.float)
        init_y = example_func_1(init_x)

        plt.plot(init_x, init_y, '.--', alpha=0.5)

        next_x = np.copy(init_x)
        next_y = np.copy(init_y)

        next_x = single_step_remeshing(next_x, next_y, delta_y=0.1, interp_func=middle_point_ceil)
        next_y = example_func_1(next_x)

        plt.plot(next_x, next_y, '.--', alpha=0.5)

        plt.show()

    def test_voltage_map(self):
        voltage_map_file = os.path.join(self.output_data_path, "3j_vmap_2.npy")

        voltage_map = np.load(voltage_map_file)
        plt.imshow(voltage_map)
        plt.show()


if __name__ == '__main__':
    unittest.main()
