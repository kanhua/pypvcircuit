"""
This script checks the installation of pypvcircuit

"""
import unittest
import os

import numpy as np
from pypvcircuit.spice_interface import SpiceConfig, solve_circuit
from pypvcircuit.config_tool import user_config_data, check_config


class EnvironmentTestCase(unittest.TestCase):
    def test_ngspice_path(self):
        spice_location = user_config_data['External programs']['spice']

        self.assertTrue(os.path.exists(spice_location), "Check if ngspice path in config file exists")

    def test_ngspice(self):
        engine = SpiceConfig.engine
        circuit = """Multiple dc sources
        v1 1 0
        r1 1 0 3.3k
        .dc v1 0 24 1
        .print dc i(v1)
        .end
            """

        data = solve_circuit(circuit, engine=engine, raw=False, postprocess_input=None)

        v = data[0, :]
        i = data[1, :]
        avg_r = np.mean(v[1:] / i[1:])
        self.assertTrue(np.isclose(3300, np.abs(avg_r)))


if __name__ == '__main__':
    unittest.main()
