import unittest
from ..quasi_3D_solver import create_node


class MyTestCase(unittest.TestCase):
    def test_1jnode(self):
        node_str = create_node(type='Bus', idx=1, idy=1, isc=[100],
                               Lx=1e-5, Ly=1e-5, rs_top=[2e-6],
                               rs_bot=[2e-6], r_shunt=[1e18], r_series=[1e-14],
                               x_metal_top=2e-16, y_metal_top=2e-16, r_contact=6e-8)

        print("print test 1J node:")
        print(node_str)
        # self.assertEqual(True, False)

    def test_3jnode(self):
        node_str = create_node(type='Bus', idx=1, idy=1, isc=[100, 200, 300],
                               Lx=1e-5, Ly=1e-5, rs_top=[1e-6, 2e-6, 3e-6],
                               rs_bot=[1e-6, 2e-6, 3e-6], r_shunt=[1e18, 2e18, 3e18],
                               r_series=[1e-14, 2e-14, 3e-14],
                               x_metal_top=2e-16, y_metal_top=2e-16, r_contact=6e-8)

        print("print test 3J node:")
        print(node_str)
        # self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
