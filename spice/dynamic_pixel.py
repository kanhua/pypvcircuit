import numpy as np
from solcore.solar_cell_solver import solar_cell_solver

from .quasi_3D_solver import create_node, create_header
from .spice import solve_circuit


def get_pixel_r(image: np.ndarray, r_x, r_y, threshold):
    """
    Calculate the aggregated resistance from a mask profile image

    :param image: an ndarray matrix
    :param r_x: resistance value per pixel in x-direction (columns, dim=1)
    :param r_y: resistance value per pixel in y-direction (rows, dim=0)
    :param threshold: threshold value of a pixel that it is a metal
    :return: aggregated resistance in x, resistance in y, metal coverage ratio
    """

    assert image.ndim == 2

    r_mask = np.where(image > threshold, 1, 0)

    metal_coverage_ratio = np.sum(r_mask).astype(np.float) / (image.shape[0] * image.shape[1])

    row_sum = np.sum(r_mask, axis=0)
    row_sum_mask = np.where(row_sum == 0, np.inf, 0)
    row_sum = row_sum_mask + row_sum

    agg_r_y = 1 / np.sum(1 / (row_sum * r_y))

    col_sum = np.sum(r_mask, axis=1)
    col_sum_mask = np.where(col_sum == 0, np.inf, 0)
    col_sum = col_sum_mask + col_sum

    agg_r_x = 1 / np.sum(1 / (col_sum * r_x))

    return agg_r_x, agg_r_y, metal_coverage_ratio


def iterate_sub_image(image, rw, cw):
    ri = np.arange(0, image.shape[0], rw, dtype=np.int)
    ci = np.arange(0, image.shape[1], cw, dtype=np.int)

    coord_set = np.empty((ri.shape[0], ci.shape[0], 4), dtype=np.uint)

    for rii in np.arange(0, ri.shape[0], 1):
        for cii in np.arange(0, ci.shape[0], 1):
            end_ri = min(ri[rii] + rw, image.shape[0])

            end_ci = min(ci[cii] + cw, image.shape[1])

            # tile = image[ri[rii]:end_ri, ci[cii]:end_ci]

            coord_set[rii, cii, 0] = ri[rii]
            coord_set[rii, cii, 1] = end_ri
            coord_set[rii, cii, 2] = ci[cii]
            coord_set[rii, cii, 3] = end_ci

    return coord_set


def generate_network(image: np.ndarray, rw: int, cw: int,
                     illumination: np.ndarray, metal_threshold,
                     isc: np.ndarray,
                     RsTop: np.ndarray,
                     RsBot: np.ndarray,
                     Rshunt,
                     Rseries,
                     Rcontact,
                     Rline,
                     Lx, Ly, gn):
    # All Resistanc related information is set here.

    SPICEbody = """"""

    coord_set = iterate_sub_image(image, rw, cw)

    r_pixels, c_pixels, _ = coord_set.shape

    # TODO: patch: default illumination
    if illumination is None:
        illumination = np.ones((r_pixels, c_pixels), dtype=np.float)

    assert illumination.shape == (r_pixels, c_pixels)

    debug_image = np.zeros((r_pixels, c_pixels))

    # We create the solar cell units and the series resistances at each node
    for xx in range(c_pixels):
        for yy in range(r_pixels):
            # This calculates the metal resistance depending on having metal on top or not. It leaves some dangling
            # resistors in the circuit, but it shouldn't be a problem.
            # metalR = max(metal * shadow[xx, yy], 1e-16) + 1e-16 * (1 - shadow[xx, yy])
            # TODO figure out how to use this equation in my situation.
            metalR = Rline / gn

            # TODO In my scheme, Lx=Ly because I don't have to recalculate sheet resistance in create_node()
            # For now I just use Lx=Ly=1 for simplicity, because create_node only calculates s=Lx/Ly

            merged_pixel_dy = coord_set[xx, yy, 1] - coord_set[xx, yy, 0]
            merged_pixel_dx = coord_set[xx, yy, 3] - coord_set[xx, yy, 2]

            sub_image = image[coord_set[xx, yy, 0]:coord_set[xx, yy, 1], coord_set[xx, yy, 2]:coord_set[xx, yy, 3]]

            merged_pixel_lx = merged_pixel_dx * Lx
            merged_pixel_ly = merged_pixel_dy * Ly

            merged_pixel_area = merged_pixel_lx * merged_pixel_ly

            pixel_area = Lx * Ly

            meta_r_x, metal_r_y, metal_coverage = \
                get_pixel_r(sub_image, r_x=metalR, r_y=metalR, threshold=metal_threshold)

            debug_image[xx, yy] = metal_coverage

            agg_contact = Rcontact / (merged_pixel_area * metal_coverage) / gn

            rsTop = RsTop / gn
            rsBot = RsBot / gn

            rseries = Rseries / merged_pixel_area / gn
            rshunt = Rshunt / merged_pixel_area / gn

            # we create a normal node
            if metal_coverage > 1e-3:
                SPICEbody = SPICEbody + create_node('Bus', xx, yy, merged_pixel_lx, merged_pixel_ly,
                                                    Isc=illumination[xx, yy] * (1 - metal_coverage) * isc,
                                                    topLCL=rsTop, botLCL=rsBot, rshunt=rshunt, rseries=rseries,
                                                    xMetalTop=meta_r_x, yMetalTop=metal_r_y, contact=agg_contact)
            else:
                SPICEbody = SPICEbody + create_node('Normal', xx, yy, merged_pixel_lx, merged_pixel_ly,
                                                    Isc=illumination[xx, yy] * isc,
                                                    topLCL=rsTop, botLCL=rsBot, rshunt=rshunt, rseries=rseries,
                                                    xMetalTop=meta_r_x, yMetalTop=metal_r_y, contact=agg_contact)

    info = dict()
    info['ynodes'] = c_pixels
    info['xnodes'] = r_pixels
    info['debug_image']=debug_image

    return SPICEbody, info


def solve_dynamic_circuit_quasi3d(vini, vfin, step, Isc, I01, I02, n1, n2, Eg, Rshunt, Rseries, injection, contacts,
                                  RsTop: np.ndarray,
                                  RsBot: np.ndarray, Rline, Rcontact, Lx, Ly,
                                  tile_rw: int, tile_cw: int):
    """ This is the function that actually dumps all the information to the Spice engine, runs the calculation, and retrieves the datafrom the calculator.

    :param vini: Initial voltage (V)
    :param vfin: Final voltage (V)
    :param step: Voltage step (V)
    :param Isc: Array of Isc for each of the junctions
    :param I01: Array of I01 for each of the junctions
    :param I02: Array of I02 for each of the junctions
    :param n1: Array of n1 for each of the junctions
    :param n2: Array of n2 for each of the junctions
    :param Eg: Array of Eg for each of the junctions
    :param Rshunt: Array of Rshunt for each of the junctions
    :param Rseries: Array of Rseries for each of the junctions
    :param injection: 2D array indicating the (optical) injection mask
    :param contacts: 2D array indicating the electrical contacts
    :param RsTop: Array of sheet resistance on the top for each of the junctions
    :param RsBot: Array of sheet resistance on the bottom for each of the junctions
    :param Rline: Resistance of the metal fingers
    :param Rcontact: Contact resistance
    :param Lx: Pixel size in the X direction
    :param Ly: Pixel size in the Y direction
    :param tile_rw: width of tile in row (Y) direction
    :param tile_cw: width of tile in column (X) direction
    :return: A tuple with:

        - V [steps + 1] : 1D Array with the external voltages
        - I [steps + 1] : 1D Array with the current at all external V
        - Vall [xnodes, ynodes, 2 * junctions, steps + 1] : 4D Array with the voltages in all nodes, at all external V
        - Vmet [xnodes, ynodes, steps + 1] : 3D Array with the voltages in the metal nodes, at all external V
    """

    # Scaling factor to bring the magnitudes to a regime where the solver is comfortable
    gn = np.sqrt(1.0 / I01[0])

    areaPerPixel = Lx * Ly * tile_cw * tile_rw

    # TODO different size of pixels exist, need different version of isc, i01 and i02

    isc = Isc * areaPerPixel * gn
    i01 = I01 * areaPerPixel * gn
    i02 = I02 * areaPerPixel * gn
    # rsTop = RsTop / gn
    # rsBot = RsBot / gn
    # rseries = Rseries / areaPerPixel / gn
    # rshunt = Rshunt / areaPerPixel / gn
    # contact = Rcontact / areaPerPixel / gn
    # metal = Rline / gn

    illumination = injection / 255
    pads = np.where(contacts > 200, 1, 0)
    shadow = np.where(contacts > 55, 1, 0)

    xnodes, ynodes = injection.shape
    junctions = len(I01)
    steps = round((vfin - vini) / step)

    SPICEheader = create_header(i01, i02, n1, n2, Eg)
    SPICEfooter = ".end"

    # We prepare the SPICE execution
    SPICEexec = ".PRINT DC i(vdep)\n.DC vdep {0} {1} {2}\n".format(vini, vfin, step)

    # Now we prepare the subcircuits on each node
    SPICEbody = """"""

    # TODO many dummy variables here for the time being
    SPICEbody, network_info = generate_network(image=contacts, rw=tile_rw, cw=tile_cw,
                                               illumination=None,
                                               metal_threshold=50,
                                               isc=isc,
                                               RsTop=RsTop,
                                               RsBot=RsBot,
                                               Rshunt=Rshunt,
                                               Rseries=Rseries,
                                               Rline=Rline,
                                               Lx=Lx, Ly=Ly, gn=gn, Rcontact=Rcontact)

    xnodes = network_info['xnodes']
    ynodes = network_info['ynodes']

    x = np.arange(xnodes)
    y = np.arange(ynodes)
    Vall = np.zeros((xnodes, ynodes, 2 * junctions, steps + 1))
    Vmet = np.zeros((xnodes, ynodes, steps + 1))
    I = np.zeros(steps + 1)
    V = np.zeros(steps + 1)

    # We combine the different bits to create the SPICE input file
    SPICEcommand = SPICEheader + SPICEbody + SPICEexec + SPICEfooter
    raw_results = solve_circuit(SPICEcommand)

    # The raw results are are a very long chunk of text. We have to clean it and pick just the info we want,
    # that is the voltages at certain nodes.
    lines = raw_results.split("\n")
    for line in lines:
        if len(line) == 0:
            continue

        if line[:5] == 'Index':
            headers = line.split()

            if len(headers) >= 4:
                indices = headers[2][4:13].split('_')
                junc = int(indices[0])
                x = int(indices[1])
                y = int(indices[2])

        if line[0] not in '01234567890.':
            continue

        i, *rest = line.split()
        i = int(i)

        if len(rest) == 3:
            Vall[x, y, 2 * junc + 1, i] = float(rest[2])
            Vall[x, y, 2 * junc, i] = float(rest[1])
        elif len(rest) == 4:
            Vall[x, y, 2 * junc + 1, i] = float(rest[2])
            Vall[x, y, 2 * junc, i] = float(rest[1])
            Vmet[x, y, i] = float(rest[3])
        else:
            V[i] = float(rest[0])
            I[i] = -float(rest[1])

    # Finally, we un-do the scaling
    I = I / gn

    return V, I, Vall, Vmet


def solve_quasi_3D(solar_cell, injection, contacts, options=None, Lx=10e-6, Ly=10e-6, h=2e-6, R_back=1e-16,
                   R_contact=1e-16, R_line=1e-16, bias_start=0, bias_end=1.8, bias_step=0.01, sub_cw=2, sub_rw=2):
    """ Entry function for the quasi-3D solver

    :param solar_cell: A solar cell object
    :param injection: 2D array indicating the (optical) injection mask
    :param contacts: 2D array indicating the electrical contacts
    :param options: Options for the 1D solar cell solver
    :param Lx: Pixel size in the X direction
    :param Ly: Pixel size in the Y direction
    :param h: Height of the metal fingers
    :param R_back: Resistance back contact
    :param R_contact: Contact resistance
    :param R_line: Resistivity metal fingers
    :param bias_start: Initial voltage (V)
    :param bias_end: Final voltage (V)
    :param bias_step: Voltage step (V)
    :param sub_cw: pixel width in column (X) direction
    :param sub_rw: pixel width in row (Y) direction
    :return: A tuple with:

        - V [steps + 1] : 1D Array with the external voltages
        - I [steps + 1] : 1D Array with the current at all external V
        - Vall [xnodes, ynodes, 2 * junctions, steps + 1] : 4D Array with the voltages in all nodes, at all external V
        - Vmet [xnodes, ynodes, steps + 1] : 3D Array with the voltages in the metal nodes, at all external V
    """
    # We first start by the solar cell as if it were a normal, isolated cell
    print("Solving 1D Solar Cell...")
    solar_cell_solver(solar_cell, 'iv', user_options=options)
    print("... Done!\n")

    # We don't care about this IV curve, in principle, but we care about some of the parameters calculated, like jsc,
    # j01 or j02 if calculated from detailed balance. We extract those parameters from the cell
    totaljuncs = solar_cell.junctions

    Isc_array = np.zeros(totaljuncs)
    I01_array = np.zeros(totaljuncs)
    n1_array = np.zeros(totaljuncs)
    I02_array = np.zeros(totaljuncs)
    n2_array = np.zeros(totaljuncs)
    Eg_array = np.zeros(totaljuncs)
    rsh_array = np.zeros(totaljuncs)
    rshTop_array = np.zeros(totaljuncs)
    rshBot_array = np.zeros(totaljuncs)
    rseries_array = np.ones(totaljuncs) * 1e-16

    for i in range(totaljuncs):

        n1_array[i] = solar_cell(i).n1 if hasattr(solar_cell(i), 'n1') else 1
        n2_array[i] = solar_cell(i).n2 if hasattr(solar_cell(i), 'n2') else 2
        rsh_array[i] = min(solar_cell(i).R_shunt, 1e16) if hasattr(solar_cell(i), 'R_shunt') else 1e16
        rshTop_array[i] = max(solar_cell(i).R_sheet_top, 1e-16) if hasattr(solar_cell(i), 'R_sheet_top') else 1e-16
        rshBot_array[i] = max(solar_cell(i).R_sheet_bot, 1e-16) if hasattr(solar_cell(i), 'R_sheet_bot') else 1e-16

        try:
            Isc_array[i] = solar_cell(i).jsc
            I01_array[i] = solar_cell(i).j01
            I02_array[i] = solar_cell(i).j02
            Eg_array[i] = solar_cell(i).Eg
        except AttributeError as err:
            raise AttributeError('ERROR in quasi-3D solver: Junction is missing one essential argument. {}'.format(err))

    j = 0
    for i in solar_cell.tunnel_indices:
        rseries_array[j] = max(solar_cell[i].R_series, 1e-16) if hasattr(solar_cell[i], 'R_series') else 1e-16
        j += 1

    rseries_array[-1] = max(R_back, 1e-16)

    print("Solving quasi-3D Solar Cell...")
    V, I, Vall, Vmet = solve_dynamic_circuit_quasi3d(bias_start, bias_end, bias_step, Isc_array, I01_array, I02_array,
                                                     n1_array,
                                                     n2_array, Eg_array, rsh_array, rseries_array, injection, contacts,
                                                     rshTop_array, rshBot_array, R_line / h, R_contact, Lx, Ly,
                                                     tile_cw=sub_cw, tile_rw=sub_rw)
    print("... Done!!")
    return V, I, Vall, Vmet