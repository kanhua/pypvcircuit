import warnings
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

    coord_set = convert_boundary_to_coordset(ci, cw, image, ri, rw)

    return coord_set


def convert_boundary_to_coordset(ci, cw, image, ri, rw):
    coord_set = np.empty((ri.shape[0], ci.shape[0], 4), dtype=np.uint)
    for rii in np.arange(0, ri.shape[0], 1):
        for cii in np.arange(0, ci.shape[0], 1):
            end_ri = min(ri[rii] + rw, image.shape[0])

            end_ci = min(ci[cii] + cw, image.shape[1])

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
