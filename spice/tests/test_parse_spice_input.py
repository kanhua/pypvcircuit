import unittest
from spice.parse_spice_input import parse_spice_command


class InputParsingTestCase(unittest.TestCase):

    def test_1(self):

        test_str_1 = "Rext0_000_002 in sn1 1e-16"

        test_str_2 = 'vdep in 0 DC 0'

        test_str_3 = 'd1_0_000_000 sn1 0 diode1_0'

        test_str_4 = 'i0_000_000 0 sn1 320.4295763908701'

        cmd_atoms = parse_spice_command(test_str_1)

        print(cmd_atoms)

        cmd_atoms = parse_spice_command(test_str_2)

        print(cmd_atoms)

        cmd_atoms = parse_spice_command(test_str_3)

        print(cmd_atoms)

        cmd_atoms = parse_spice_command(test_str_4)

        print(cmd_atoms)
