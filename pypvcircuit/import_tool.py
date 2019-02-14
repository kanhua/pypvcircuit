from struct import unpack
import pandas as pd
import numpy as np


def to_ill_mtx(df: pd.DataFrame, r_pixel=100, c_pixel=100,
               r_max=None, r_min=None, c_max=None, c_min=None,
               r_coord='x', c_coord='z'):
    columns = ['x', 'y', 'z', 'l', 'm', 'n', 'power', 'wavelength']

    assert set(df.columns) == set(columns)

    df = df.sort_values(by=['wavelength'])

    all_wavelength = df['wavelength'].unique()

    c_max, c_min, r_max, r_min = _check_boundary(c_coord, c_max, c_min, df, r_coord, r_max, r_min)

    # initilize the 3D array for storing the matrix.
    # Note that all elements should be zeros.
    ill_mtx = np.zeros((r_pixel, c_pixel, all_wavelength.size))

    dr = (r_max - r_min) / r_pixel
    dc = (c_max - c_min) / c_pixel

    r_index = np.floor_divide(df[r_coord] - r_min, dr).astype(np.uint)
    c_index = np.floor_divide(df[c_coord] - c_min, dc).astype(np.uint)

    df['i'] = r_index
    df['j'] = c_index

    df['ij'] = r_index * r_pixel + c_index

    sel_col = ['power', 'wavelength', 'ij']
    grouped = df.loc[:, sel_col].groupby('wavelength')

    for wavelength, subgroup in grouped:
        mtx = subgroup.groupby('ij').sum()

        ij_value = mtx.index.values
        r_index = np.floor_divide(ij_value, r_pixel)
        c_index = np.mod(ij_value, r_pixel)

        print("wavelength: {}".format(wavelength))
        index = np.searchsorted(all_wavelength, wavelength)
        ill_mtx[r_index, c_index, index] = mtx['power']

    return ill_mtx, all_wavelength


def _check_boundary(c_coord, c_max, c_min, df, r_coord, r_max, r_min):
    if r_max is None:
        r_max = np.max(df[r_coord])
    else:
        if r_max <= np.max(df[r_coord]):
            raise ValueError("r_max is out of bound")
    if c_max is None:
        c_max = np.max(df[c_coord])
    else:
        if c_max <= np.max(df[c_coord]):
            raise ValueError("c_max is out of bound")
    if r_min is None:
        r_min = np.min(df[r_coord])
    else:
        if r_min > np.min(df[r_coord]):
            raise ValueError("r_min is out of bound")
    if c_min is None:
        c_min = np.min(df[c_coord])
    else:
        if c_min > np.min(df[c_coord]):
            raise ValueError("c_min is out of bound")
    return c_max, c_min, r_max, r_min


class RayData(object):

    def __init__(self, filename):
        self.df = None
        self.wavelength = None
        int_byte = 4
        float_byte = 4

        fp = open(filename, 'rb')

        dbyte = fp.read(int_byte)
        self.signature = unpack('cccc', dbyte)
        sig_char = [x.decode("ASCII") for x in self.signature]
        self.signature = ''.join(sig_char)
        assert self.signature == "LTRF"  # check if the file is legal

        dbyte = fp.read(int_byte * 6)
        self.major_version, self.minor_version, \
        self.data_type, self.far_field, self.color_info, \
        self.length_units = unpack('i' * 6, dbyte)

        # currently we only support type 2 file
        assert self.color_info == 2

        dbyte = fp.read(float_byte * 4)
        self.x0, self.y0, self.z0, self.flux = unpack('f' * 4, dbyte)

        self.data_array = []
        # Check if last line is encountered
        # Read the first 7 bytes
        while True:
            dbyte = fp.read(7)
            end_string = unpack('c' * 7, dbyte)
            end_char = ''
            try:
                end_char = [x.decode('ASCII') for x in end_string]
                end_char = ''.join(end_char)
            except UnicodeDecodeError:
                pass
            if end_char == 'LTRFEND':
                break
            else:
                other_bytes = fp.read(25)
                all_dbytes = b''.join([dbyte, other_bytes])
                data = unpack('f' * 8, all_dbytes)
                data = list(data)
                self.data_array.extend(data)

        rows = int(len(self.data_array) / 8)
        self.data_array = np.array(self.data_array).reshape((rows, 8))

    def sort_array(self):

        columns = ['x', 'y', 'z', 'l', 'm', 'n', 'power', 'wavelength']

        self.df = pd.DataFrame(self.data_array, columns=columns)

        self.ill_mtx, self.wavelength = to_ill_mtx(self.df)

    def sel_wavelength(self, selected_wavelength):

        wdf = self.df.loc[self.df['wavelength'] == selected_wavelength, :]

        return wdf


if __name__ == "__main__":
    rd = RayData("public_data/exporty_rays_binary.1.ray")
    print(rd.signature)
    print(rd.major_version)
    print("data type: {}".format(rd.data_type))
    print("Color info: {} ".format(rd.color_info))
    print("origin x: {}".format(rd.x0))
    print("origin y: {}".format(rd.y0))
    print("origin z: {}".format(rd.z0))
    print(rd.data_array)

    rd.sort_array()
    print(rd.df.head())
    print(rd.df['wavelength'].unique())
    print(rd.df.shape)

    import matplotlib.pyplot as plt

    plt.imshow(rd.ill_mtx[:, :, 0])
    plt.show()
