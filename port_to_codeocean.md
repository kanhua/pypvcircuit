# Notes of uploading this repo to CodeOcean

1. Copy all the data in ```./public_data``` into ```/data``` in CodeOcean repository.

2. Delete ```./experiment``` folder.

3. In the jupyter notebook starter file, add the following setup setting:

```bash
python setup_spice.py ngspice /results /results
```

3. Post-installation scripts
```bash
pip install git+https://github.com/kanhua/pypvcell.git
ln -s ../data/ ../code/public_data/
export PYTHONPATH=$PYTHONPATH:"/code"
python setup_spice.py ngspice /results /results
```


```bash
#!/usr/bin/env bash
set -ex

mkdir -p ../code/public_data
ln -s ../data/public_data/ ../code/public_data/
ln -s ../data/concentrated_3j_iv.csv ../code/concentrated_3j_iv.csv
ln -s ../data/example_ray.csv ../code/tests/example_ray.csv

# This is the master script for the capsule. When you click "Reproducible Run", the code in this file will execute.
bash run_demo_suites.sh 

jupyter nbconvert \
  --ExecutePreprocessor.allow_errors=True \
  --ExecutePreprocessor.timeout=-1 \
  --output-dir=../results \
  --execute 'network simulation demo.ipynb'

```