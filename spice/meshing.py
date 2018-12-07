import math
import warnings
import typing
import numpy as np
from scipy.interpolate import interp2d


def get_merged_r_image(mask_image: np.ndarray, rw, cw):
    """
    Generate merged resistance image

    :param mask_image: mask image array
    :param rw: row pixel width of the sub-image
    :param cw: column pixel width of the sub-image
    :return: the merged mask image
    """

    sub_image_coord = iterate_sub_image(mask_image, rw, cw)
    agg_image = get_merged_r_image_from_coordset(mask_image, sub_image_coord)

    return agg_image


def get_merged_r_image_from_coordset(mask_image, sub_image_coord):
    agg_image = np.zeros((sub_image_coord.shape[0], sub_image_coord.shape[1]))
    for i in range(sub_image_coord.shape[0]):
        for j in range(sub_image_coord.shape[1]):
            a, b, c, d = sub_image_coord[i, j, :]
            agg_image[i, j] = np.sum(mask_image[a:b, c:d])
    return agg_image


def resize(image, new_shape):
    """
    Simple reszing procedure. Suitable for resizing illumination profile.

    :param image: the input image
    :param new_shape: target array shape tuple(new_x_dim,new_y_dim)
    :return: the resized image
    """
    warnings.warn("Use resize_illumination() instead", DeprecationWarning)

    assert image.ndim == 2

    # corner case
    if image.shape == new_shape:
        return image

    row_index = np.arange(0, image.shape[0], 1)
    col_index = np.arange(0, image.shape[1], 1)
    image_func = interp2d(col_index, row_index, image)
    x_new = np.linspace(0, image.shape[0], num=new_shape[0])
    y_new = np.linspace(0, image.shape[1], num=new_shape[1])

    resized_image = image_func(y_new, x_new)

    assert resized_image.shape == new_shape
    return resized_image


def iterate_sub_image(image, rw, cw):
    ri = np.arange(0, image.shape[0], rw, dtype=np.int)
    ci = np.arange(0, image.shape[1], cw, dtype=np.int)

    coord_set = convert_boundary_to_coordset(image.shape, ri, ci)

    return coord_set


def convert_boundary_to_coordset(image_shape, ri, ci):
    coord_set = np.empty((ri.shape[0], ci.shape[0], 4), dtype=np.uint)
    for rii in np.arange(0, ri.shape[0], 1):
        for cii in np.arange(0, ci.shape[0], 1):

            if rii == ri.shape[0] - 1:
                end_ri = image_shape[0]
            else:
                end_ri = ri[rii + 1]

            if cii == ci.shape[0] - 1:
                end_ci = image_shape[1]
            else:
                end_ci = ci[cii + 1]

            coord_set[rii, cii, 0] = ri[rii]
            coord_set[rii, cii, 1] = end_ri
            coord_set[rii, cii, 2] = ci[cii]
            coord_set[rii, cii, 3] = end_ci
    return coord_set


def resize_illumination(illumination, contact_mask, coord_set: np.array, threshold=0):
    assert illumination.shape == contact_mask.shape
    light_mask = (contact_mask > threshold)

    filtered_illumination = illumination * light_mask

    r_pixels, c_pixels, _ = coord_set.shape

    resized_illumination = np.empty((r_pixels, c_pixels))

    for c_index in range(c_pixels):
        for r_index in range(r_pixels):
            sub_image = filtered_illumination[coord_set[r_index, c_index, 0]:coord_set[r_index, c_index, 1],
                        coord_set[r_index, c_index, 2]:coord_set[r_index, c_index, 3]]

            resized_illumination[r_index, c_index] = np.sum(sub_image)

    return resized_illumination


def resize_illumination_3d(illumination: np.ndarray, contact_mask,
                           coord_set: np.array, threshold=0):
    assert illumination.ndim == 3
    assert illumination[:, :, 0].shape == contact_mask.shape

    # stupid method for resizing. Need to figure out a faster way to do this
    r_pixels, c_pixels, _ = coord_set.shape

    resized_illumination = np.empty((r_pixels, c_pixels, illumination.shape[2]))

    for zi in range(illumination.shape[2]):
        resized_illumination[:, :, zi] = resize_illumination(illumination[:, :, zi], contact_mask, coord_set, threshold)

    return resized_illumination


class MeshGenerator(object):
    """
    A class that handles the meshing.

    ci is the sequence of the selected row index, i.e., the position of the meshgrid on original image index.
    For example, if the original image is 10x10 and the initial step size is 2, then
    ci is 0, 2, 4, 6, 8, and same as ri.


    """

    def __init__(self, image_shape: typing.Tuple[int, int], rw: int, cw: int):

        # historical mesh data saved here after running refine()
        self.r_hist = []
        self.c_hist = []

        self.raw_image_shape = image_shape

        self.current_ri = np.arange(0, image_shape[0], rw, dtype=np.int)
        self.current_ci = np.arange(0, image_shape[1], cw, dtype=np.int)

    def ci(self):
        return self.current_ci

    def ri(self):
        return self.current_ri

    def to_coordset(self):
        return convert_boundary_to_coordset(self.raw_image_shape, self.ri(), self.ci())

    def refine(self, y, delta_y, dim: int):

        assert (dim == 0 or dim == 1)

        # xg is original index
        if dim == 0:
            xg = self.current_ri
            self.r_hist.append(np.copy(self.current_ri))
        else:
            xg = self.current_ci
            self.c_hist.append(np.copy(self.current_ci))

        nx = single_step_remeshing(xg, y, delta_y, interp_func=middle_point_ceil)

        if dim == 0:
            self.current_ri = nx
        else:
            self.current_ci = nx


def single_step_remeshing(x, y, delta_y, interp_func):
    index_to_be_add = []
    for xi, xval in enumerate(x[:-1]):

        if np.abs(y[xi + 1] - y[xi]) >= delta_y:
            index_to_be_add.append(xi)

    if len(index_to_be_add) == 0:
        warnings.warn("No new index added.", UserWarning)
        return x

    nxval = interp_func(index_to_be_add, x)

    nx = np.insert(x, np.array(index_to_be_add) + 1, nxval)

    return nx


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
