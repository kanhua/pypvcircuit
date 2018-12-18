import unittest
from pypvcircuit.parse_spice_output import parse_output

class MyTestCase(unittest.TestCase):
    def test_parse(self):
        with open("for_spice_out_test.txt", 'r') as fp:
            raw_results = fp.read()

        result = parse_output(raw_results)

        V, I = result['dep#branch']

        V2, V2p = result['(t_0_000_001)']

        import matplotlib.pyplot as plt

        plt.plot(V2, V2p)
        plt.show()

if __name__ == '__main__':
    unittest.main()
