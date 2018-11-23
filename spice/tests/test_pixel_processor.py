import unittest
from pypvcell.solarcell import SQCell
from spice.pixel_processor import PixelProcessor



class PixelProcessorTestCase(unittest.TestCase):

    def test_1(self):
        sq = SQCell(1.42, 300, 1)
        from pypvcell.illumination import load_astm

        ill = load_astm("AM1.5g")
        sq.set_input_spectrum(ill)
        px = PixelProcessor(sq, lx=1e-6, ly=1e-6)
        print(px.node_string())








if __name__ == '__main__':
    unittest.main()
