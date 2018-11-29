import unittest
from spice.parse_spice_input import parse_spice_command


class InputParsingTestCase(unittest.TestCase):

    def test_basic_parsing(self):
        test_str_1 = "Rext0_000_002 in sn1 1e-16"

        test_str_2 = 'vdep in 0 DC 0'

        test_str_3 = 'd1_0_000_000 sn1 0 diode1_0'

        test_str_4 = 'i0_000_000 0 sn1 320.4295763908701'

        cmd_atoms = parse_spice_command(test_str_1)

        self.assertEqual(cmd_atoms['name'], 'Rext0_000_002')
        self.assertEqual(cmd_atoms['p_node'], 'in')
        self.assertEqual(cmd_atoms['n_node'], 'sn1')
        self.assertEqual(cmd_atoms['value'], 1e-16)

        cmd_atoms = parse_spice_command(test_str_2)

        self.assertEqual(cmd_atoms['name'], 'vdep')

        cmd_atoms = parse_spice_command(test_str_3)

        self.assertEqual(cmd_atoms['name'], 'd1_0_000_000')
        self.assertEqual(cmd_atoms['value'], 'diode1_0')

        cmd_atoms = parse_spice_command(test_str_4)

        self.assertEqual(cmd_atoms['name'], 'i0_000_000')
        self.assertAlmostEqual(cmd_atoms['value'], 320.4295763908701)
