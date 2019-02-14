# How to install (Windows PowerShell script)

## Prerequisites
This script will download and install the following software:

1. [Anaconda](https://www.anaconda.com/) or [Miniconda](https://conda.io/miniconda.html): A python language distribution made for scientific computing.
2. NGSpice: A circuit network library

All the software will be installed in a folder of your choice.
Installation of this software suite will not require the authorization of administrator of the OS.


## Install pypvcell

```bash
pip install git+git://github.com/kanhua/pypvcell
```


## Download pypvcircuit package

If you have git:

```bash
git clone https://github.com/kanhua/solar-cell-circuit.git

```

or you could just download the zip

![download](doc_images/download_clone.png)

## Run setup file

Run
```bash

python setup_spice.py SPICEPATH OUTPUTPATH


```


## Set PYTHONPATH




