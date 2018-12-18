import unittest
import os
import math
import numpy as np

import matplotlib.pyplot as plt

from skimage.io import imread

from pypvcircuit.meshing import single_step_remeshing, \
    middle_point_ceil, middle_point, MeshGenerator
from .helper import get_quater_image


def example_func_1(x):
    return 1 / np.power(x, 2)


def example_func_2(x, T=50):
    return np.sin(np.pi * 2 / T * x)


class AdaptiveMeshTestCase(unittest.TestCase):

    def setUp(self):
        self.file_path = os.path.abspath(os.path.dirname(__file__))

        self.output_data_path = os.path.join(self.file_path, 'test_output_data')

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

    def test_view_voltage_map(self):
        voltage_map_file = os.path.join(self.output_data_path, "3j_vmap_5.npy")

        voltage_map = np.load(voltage_map_file)

        fig, ax = plt.subplots(nrows=1, ncols=2)

        middle_r = math.ceil(voltage_map.shape[0] / 2)

        ax[1].plot(voltage_map[middle_r, :])

        ax[0].imshow(voltage_map)
        plt.show()

    def test_ex_func2(self):

        x = np.linspace(0, 100, num=101)

        plt.plot(x, example_func_2(x))
        plt.show()

    def test_mesh_refine(self):
        mx = MeshGenerator((100, 100), rw=20, cw=20)

        init_y = example_func_2(mx.current_ci.astype(np.float))

        plt.plot(mx.current_ci, init_y, '.--')

        next_y = np.copy(init_y)

        for i in range(3):
            mx.refine(next_y, delta_y=0.01, dim=1)

            next_y = example_func_2(mx.current_ci.astype(np.float))

            plt.plot(mx.current_ci, next_y, '.--')

        plt.show()

    def test_failed_mesh_refine(self):
        """
        Set the initial period with exactly the same as the period of the sine function.
        This result shows that this algorithm only works for (locally) monotonic function

        :return:
        """

        mx = MeshGenerator((100, 100), rw=10, cw=10)

        init_y = example_func_2(mx.current_ci.astype(np.float), T=10)

        plt.plot(mx.current_ci, init_y, '.--')

        next_y = np.copy(init_y)

        for i in range(3):
            mx.refine(next_y, delta_y=0.01, dim=1)

            next_y = example_func_2(mx.current_ci.astype(np.float), T=10)

            plt.plot(mx.current_ci, next_y, '.--')

        plt.show()

    def test_slice_voltage_map(self):
        """
        slicing on the voltage map and view the results

        :return:
        """

        voltage_map_file = os.path.join(self.output_data_path, "3j_vmap_5.npy")

        voltage_map = np.load(voltage_map_file)

        middle_r = math.ceil(voltage_map.shape[0] / 2)

        rep_voltage = voltage_map[middle_r, :]

        mask = imread(os.path.join(self.file_path, 'masks_sq.png'), as_grey=True)
        mask = get_quater_image(mask)

        mx = MeshGenerator(mask.shape, rw=5, cw=5)

        plt.plot(mx.ci(), rep_voltage)

        mx.refine(y=rep_voltage, delta_y=0.1, dim=1)

        plt.vlines(mx.ci(), ymin=np.min(rep_voltage), ymax=np.max(rep_voltage),
                   alpha=0.5, linewidths=1, colors='r')

        plt.show()


if __name__ == '__main__':
    unittest.main()
