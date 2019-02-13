from struct import unpack
import pandas as pd
import numpy as np


class RayData(object):

    def __init__(self, filename):
        self.df = None
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
        self.df = self.df.sort_values(by=['wavelength'])

        wavelength = self.df['wavelength'].unique()

        r_min = np.min(self.df['x'])
        r_max = np.max(self.df['x'])

        c_min = np.min(self.df['z'])
        c_max = np.max(self.df['z'])

        r_pixel = 100
        c_pixel = 100

        dr = (r_max - r_min) / r_pixel
        dc = (c_max - c_min) / c_pixel

        r_index = np.floor_divide(self.df['x'] - r_min, dr)
        c_index = np.floor_divide(self.df['z'] - c_min, dc)

        self.df['i'] = r_index
        self.df['j'] = c_index

        self.df['ij'] = r_index * r_pixel + c_index

        grouped = self.df.groupby('ij').sum()
        print(grouped)

        # grouped


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
    print(rd.df['i'].unique().size)
    print(rd.df['j'].unique().size)
    print(rd.df.shape)
