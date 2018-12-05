import unittest
import os
import math
import numpy as np

import matplotlib.pyplot as plt

import warnings


def example_func_1(x):
    return 1 / np.power(x, 2)


def middle_point(xi, x):
    """
    Add new points into all the x[xi] and x[xi+1].
    Let's denote these values as x[xi+0.5]

    :param xi: indices that will be added into x
    :param x: array that will be added
    :return: interpolated values of all x[xi+0.5]. the size is the same as xi
    """
    xi_a = np.array(xi, dtype=np.uint)

    average = (x[xi_a] + x[xi_a + 1]) / 2

    return average


def middle_point_ceil(nxi, x0):
    """
    Add new points into all the x[xi] and x[xi+1].
    Let's denote these values as x[xi+0.5]

    :param nxi: indices that will be added into x
    :param x: array that will be added
    :return: interpolated values of all x[xi+0.5]. the size is the same as xi
    """
    nxval = []

    for i in nxi:
        val = math.floor((x0[i] + x0[i + 1]) / 2)
        nxval.append(val)
    return nxval


def single_step_remeshing(x, y, delta_y, interp_func):
    index_to_be_add = []
    for xi, xval in enumerate(x[:-1]):

        if np.abs(y[xi + 1] - y[xi]) > delta_y:
            index_to_be_add.append(xi)

    if len(index_to_be_add) == 0:
        warnings.warn("No new index added.", UserWarning)
        return x

    nxval = interp_func(index_to_be_add, x)

    nx = np.insert(x, np.array(index_to_be_add) + 1, nxval)

    return nx


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
            next_x = single_step_remeshing(next_x, next_y, delta_y=0.1,interp_func=middle_point)
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
