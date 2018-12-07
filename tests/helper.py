import os
import numpy as np
import matplotlib.pyplot as plt

from skimage.io import imread
from spice.meshing import get_merged_r_image

from pypvcell.solarcell import SQCell


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


def load_common_setting(test_instance):
    file_path = os.path.abspath(os.path.dirname(__file__))

    test_instance.output_data_path = os.path.join(file_path, 'test_output_data')

    test_instance.T = 298

    # TODO simplify the illumination mask to np.ones
    # self.default_illuminationMask = imread(os.path.join(file_path, 'masks_illumination.png'))

    test_instance.default_contactsMask = imread(os.path.join(file_path, 'masks_sq_no_shades.png'))

    test_instance.default_illuminationMask = np.ones_like(test_instance.default_contactsMask) * 100

    # Size of the pixels (m)
    test_instance.lr = 10e-5
    test_instance.lc = 10e-5

    # Height of the metal fingers (m)
    test_instance.h = 2.2e-6

    # Contact resistance (Ohm m2)
    test_instance.Rcontact = 3e-10

    # Resistivity metal fingers (Ohm m)
    test_instance.Rline = 2e-8

    # Bias (V)
    test_instance.vini = 0
    test_instance.vfin = 3.0
    test_instance.step = 0.05

    test_instance.gaas_1j = SQCell(1.42, 300, 1)
    test_instance.ingap_1j = SQCell(1.87, 300, 1)

    return test_instance


def draw_illumination_3d(illumination: np.ndarray, wavelength: np.ndarray,
                         plot_index: np.ndarray):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(nrows=1, ncols=len(plot_index))

    for idx in range(len(plot_index)):
        ax[idx].set_title("{:.1f} nm".format(wavelength[plot_index[idx]]))
        ax[idx].imshow(illumination[:, :, plot_index[idx]])
    return fig, ax


def contact_ratio(mask_image, threshold):
    n = mask_image.size

    m = np.sum(np.where(mask_image > threshold, 1, 0))

    return float(m) / float(n)
