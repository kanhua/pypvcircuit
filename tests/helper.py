import os
import numpy as np
import matplotlib.pyplot as plt
from spice.dynamic_pixel import get_merged_r_image


def draw_merged_contact_images(output_data_path, test_pws, file_prefix: str, contact_mask: np.ndarray):
    """
    Output an image "{}equiv_r_images.png".format(file_prefix)) to compare the contact images
    and their merged versions.

    :param test_pws: a list of different pixel widths
    :param file_prefix: prefix of the file.
    :param contact_mask: The profile of the metal contact
    :return:
    """

    fig, ax = plt.subplots(ncols=len(test_pws) + 1, figsize=(8, 6), dpi=300)
    for i, pw in enumerate(test_pws):
        r_image = get_merged_r_image(contact_mask, pw, pw)
        ax[i].imshow(r_image)
        ax[i].set_title("{} pixels".format(pw))
    r_image = get_merged_r_image(contact_mask, 1, 1)
    ax[-1].imshow(r_image)
    ax[-1].set_title("original")
    fig.savefig(os.path.join(output_data_path, "{}equiv_r_images.png".format(file_prefix)))
    plt.close(fig)


def draw_contact_and_voltage_map(output_data_path, test_pws, file_prefix: str, contact_mask: np.ndarray):
    fig, ax = plt.subplots(nrows=2, ncols=len(test_pws) + 1, figsize=(8, 6), dpi=300)
    for i, pw in enumerate(test_pws):
        r_image = get_merged_r_image(contact_mask, pw, pw)
        ax[0, i].imshow(r_image)
        ax[0, i].set_title("{} pixels".format(pw))

        voltage_map = np.load(os.path.join(output_data_path, "{}_vmap_{}.npy").format(file_prefix, pw))

        ax[1, i].imshow(voltage_map)

    r_image = get_merged_r_image(contact_mask, 1, 1)
    ax[0, -1].imshow(r_image)
    ax[0, -1].set_title("original")
    fig.savefig(os.path.join(output_data_path, "{}_equiv_r_map_images.png".format(file_prefix)))
    plt.close(fig)


def get_quater_image(image: np.ndarray):
    nx, ny = image.shape

    # For symmetry arguments (not completely true for the illumination), we can mode just 1/4 of the device and then
    # multiply the current by 4
    center_x = int(nx / 2)
    center_y = int(ny / 2)
    return image[center_x:, center_y:]
