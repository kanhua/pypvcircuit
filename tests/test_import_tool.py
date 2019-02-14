import unittest
from pypvcircuit.import_tool import to_ill_mtx
import pandas as pd


class ImportToolTestCase(unittest.TestCase):
    def test_to_ill_mtx(self):
        df = pd.read_csv("example_ray.csv")

        mtx, _ = to_ill_mtx(df, r_pixel=10, c_pixel=10, r_max=5,
                            r_min=-5, c_max=5, c_min=-5)

        self.assertEqual(mtx.shape[2], 2)
        self.assertEqual(mtx[0, -1, 0], 2)


if __name__ == '__main__':
    unittest.main()
