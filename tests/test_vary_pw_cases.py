import os
import numpy as np
from skimage.io import imread

from pypvcell.solarcell import SQCell, MJCell

from pypvcircuit.util import make_3d_illumination, gen_profile, HighResGrid, MetalGrid

from tests.helper import draw_contact_and_voltage_map, draw_merged_contact_images, \
    get_quater_image, contact_ratio, draw_illumination_3d

from tests.exp_vary_pw import PWExp


def baseline_case():
    file_path = os.path.abspath(os.path.dirname(__file__))

    contacts_mask = imread(os.path.join(file_path, 'masks_sq_no_shades.png'))

    contacts_mask = get_quater_image(contacts_mask)

    illumination_mask = np.ones_like(contacts_mask)

    mg = MetalGrid()
    mg.metal_image = contacts_mask
    mg.lr = 1e-5
    mg.lc = 1e-5

    gaas_1j = SQCell(1.42, 300, 1)

    pe = PWExp(illumination_mask, mg, vini=0, vfin=1.2, vstep=0.05, test_pixel_width=[1, 2, 5, 10], file_prefix="t1")

    pe.vary_pixel_width(gaas_1j)

    pe.plot_time()


def highres_case():
    mg = HighResGrid()

    contacts_mask = mg.metal_image

    contacts_mask = get_quater_image(contacts_mask)

    illumination_mask = np.ones_like(contacts_mask)

    mg.metal_image = contacts_mask
    mg.lr = 1e-6
    mg.lc = 1e-6

    gaas_1j = SQCell(1.42, 300, 1)

    pe = PWExp(illumination_mask, mg, vini=0, vfin=1.2, vstep=0.02, test_pixel_width=[5, 10, 15], file_prefix="t2")

    pe.vary_pixel_width(gaas_1j)

    pe.plot_time()


baseline_case()

# highres_case()
