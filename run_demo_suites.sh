#!/bin/bash
#this script runs through the settings
export PYTHONPATH=$PYTHONPATH:"~/capsule/code"
python setup_spice.py ngspice /results
python ./tests/test_vary_pw_cases.py