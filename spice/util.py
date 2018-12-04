import math
import numpy as np
import typing
import warnings


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

    if finger_width_p<1:
        warnings.warn("The width of the finger is zero",RuntimeWarning)

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
    lr = image.shape[0]
    lc = image.shape[1]

    bus_width_p = int(lr * bus_width)
    margin_r_p = int(image.shape[0] * margin_r)
    margin_c_p = int(image.shape[1] * margin_c)

    image[margin_r_p:margin_r_p + bus_width_p, margin_c_p:lc - margin_c_p] = 255

    image[lr - margin_r_p - bus_width_p:lr - margin_r_p, margin_c_p:lc - margin_c_p] = 255

    return image
