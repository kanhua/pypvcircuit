"""
Utility functions for generating metal or illumination mask profile

"""

import numpy as np
import typing
import warnings

from pypvcell.illumination import load_astm


class MetalGrid(object):
    def __init__(self):
        self.metal_image = np.zeros((1, 1))  # dummy image
        self.lr = 0
        self.lc = 0

    def get_binary_image(self):
        return np.where(self.metal_image > 0, 1, 0)

    def get_lc(self):
        return self.lc

    def get_lr(self):
        return self.lr


class HighResGrid(MetalGrid):

    def __init__(self):
        image_shape = (1000, 1000)
        finger_n = 10
        test_image = np.zeros(image_shape, dtype=np.uint8)
        test_image = add_grid(test_image, finger_n, 0.01, 0.01)
        test_image = add_busbar(test_image, bus_width=0.1, margin_c=0.02, margin_r=0.02)

        self.metal_image = test_image
        self.lr = 1e-6
        self.lc = 1e-6


def default_mask(image_shape: typing.Tuple[int, int], finger_n: int):
    """
    Generate a typical mask design from an image
    
    :param image_shape: the shape of the generated image
    :param finger_n: number of fingers
    :return: the generated image
    """
    test_image = np.zeros(image_shape, dtype=np.uint8)
    test_image = add_grid(test_image, finger_n, 0.02, 0.02)
    test_image = add_busbar(test_image, bus_width=0.1, margin_c=0.02, margin_r=0.02)

    return test_image


def add_grid(image: np.ndarray, finger_n, finger_width, margin_c) -> np.ndarray:
    """
    Add fingers on the mask image. The fingers is parallel to the column (vertical) direction.
    The input image will be overwritten.

    :param image: the input image to be modified
    :param finger_n: number of grids
    :param finger_width: width of finger in pixels
    :param margin_c: fraction margin of the top and bottom ends (in column)
    :return: the modified image.
    """

    margin_c_p = int(image.shape[1] * margin_c) + 1

    lr = image.shape[0]
    lc = image.shape[1]

    finger_width_p = int(finger_width * lc)

    if finger_width_p < 1:
        warnings.warn("The width of the finger is zero", RuntimeWarning)

    pitch = lc // finger_n

    remainder = lc % finger_n

    finger_pos = np.linspace(pitch + remainder // 2, lc - pitch - remainder // 2, num=finger_n, dtype=np.uint)

    for pos in finger_pos:
        r0 = margin_c_p
        assert type(r0) == int
        r1 = lr - margin_c_p
        assert type(r1) == int

        c0 = int(pos - finger_width_p // 2)
        c1 = int(pos + finger_width_p // 2)

        assert type(c0) == int
        assert type(c1) == int

        assert c0 >= 0
        assert c1 >= 0

        image[margin_c_p:lr - margin_c_p, c0:c1] = 124

    return image


def add_busbar(image: np.ndarray, bus_width, margin_r, margin_c):
    """
    Add horizontal bus bar onto both end of the image.
    The pixel value of the bus bar is 255.
    In this version, the bus bar draws on the input image, that is, the input image will be modified.

    :param image: the input image
    :param bus_width: the bus bar width in fraction of image.shape[0]
    :param margin_r: the width between the bus bar and the edge of the cell in vertical (row) direction
    :param margin_c: the width between the bus bar and the edge of the cell in horizontal (vertical) direction
    :return:
    """

    lr = image.shape[0]
    lc = image.shape[1]

    bus_width_p = int(lr * bus_width)
    margin_r_p = int(image.shape[0] * margin_r)
    margin_c_p = int(image.shape[1] * margin_c)

    image[margin_r_p:margin_r_p + bus_width_p, margin_c_p:lc - margin_c_p] = 255

    image[lr - margin_r_p - bus_width_p:lr - margin_r_p, margin_c_p:lc - margin_c_p] = 255

    return image


def gen_profile(rows, cols, bound_ratio, conc=1):
    """
    Randomly generate a profile I(r,c), so that:

    1) The shape of I(r,c) is (rows,cols)

    2) sum(I(r,c))=conc*rows*cols

    3) I(r,c)==0 when r>rows*bound_ratio and c>cols*bound_ratio

    :param rows: number of rows of the profile matrix
    :param cols: number of columns of the profile matrix
    :param bound_ratio: position of the bound (in fraction)
    :param conc: average concentration
    :return:
    """
    total_power_pixel = rows * cols * conc
    left_bound_x = np.floor(rows * bound_ratio).astype(np.int)
    left_bound_y = np.floor(cols * bound_ratio).astype(np.int)
    xp = np.random.randint(0, left_bound_x, size=total_power_pixel)
    yp = np.random.randint(0, left_bound_y, size=total_power_pixel)
    zmtx = np.zeros((rows, cols))
    for i in range(xp.shape[0]):
        zmtx[xp[i], yp[i]] += 1
    return zmtx


class LinearAberration(object):

    def __init__(self, x0, x1, y0, y1):
        """
        Define a linear chromatic aberration y(x) functor by interpolation
        y is a response function that can be used, for example, as the bound_value in gen_profile()
        Note that this function converts wavelength to frequency

        :param x0: wavelength 0
        :param x1: wavelength 1
        :param y0: the responded value of x0
        :param y1: the responded value of x1
        """
        x0 = 1 / x0
        x1 = 1 / x1

        self.m = (y0 - y1) / (x0 - x1)
        self.b = -self.m * x0 + y0

    def get_abb(self, wavelength):
        """
        Get the interpolated value x
        :param wavelength:
        :return: y value
        """
        x = 1 / wavelength

        return x * self.m + self.b


def make_3d_illumination(rows: int, cols: int) -> typing.Tuple[np.ndarray, np.ndarray]:
    """
    Make a three dimensional illumination I(x,y,z)

    :param rows: number of rows
    :param cols: number of columns
    :return: illumination matrix, wavelengths in nm
    """
    default_illumination = load_astm("AM1.5g")
    spec = default_illumination.get_spectrum(to_x_unit='nm')
    wavelength = spec[0, :]
    lb = LinearAberration(np.max(wavelength), np.min(wavelength), 0.9, 0.6)
    bound = lb.get_abb(wavelength)
    ill_mtx = np.empty((rows, cols, wavelength.shape[0]))
    for zi in range(ill_mtx.shape[2]):
        ill_mtx[:, :, zi] = gen_profile(rows, cols, bound_ratio=bound[zi])
    return ill_mtx, spec[0, :]
