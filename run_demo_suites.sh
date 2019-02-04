#!/bin/bash
#this script runs through the settings
export PYTHONPATH=$PYTHONPATH:"/code"
python setup_spice.py ngspice /results

echo "running test cases"
cd tests
python -m unittest test_vary_pw_cases.PaperFigure.test_triang_3j