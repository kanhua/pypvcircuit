#!/bin/bash
#this script runs through the settings
export PYTHONPATH=$PYTHONPATH:"/code"
python setup_spice.py ngspice /results

echo "running test cases"
cd tests
python -m unittest test_vary_pw_cases.PaperFigure

cd ../diagnostics
python plot_yaml_data.py highres_triang_1x_dataset.yaml
python plot_yaml_data.py highres_triang_500x_dataset.yaml
python plot_yaml_data.py highres_triang_500x_10mm_dataset.yaml