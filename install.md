# How to install Solcore5 and ngspice

## Overview
This script will download and install the following software:

1. [Miniconda](https://conda.io/miniconda.html): A python language distribution made for scientific computing.
2. Solcore5: A solar cell modeling library written in python
3. NGSpice: A circuit network library

All the software will be installed in a folder of your choice.
Installion of this software suite will not require the autorization of administrator of the OS.

## Install the software suite

### Step 1: Change ExecutionPolicy setting

Reason for this step: by default, Powershell does not allow the execution of third-party powershell script.
We therefore have to allow it to do that temporarily.

1. Run Windows Powershell as administrator. [This page](https://msdn.microsoft.com/en-us/library/dn568022.aspx) shows how to do this.
2. Open Powershell, in the powershell command line, run the following script

```
> Set-ExecutionPolicy Unrestricted
```

### Step 2: Run the installtion script

1. In Powershell, run

```
solcore5_install.ps1 > Out-File -FilePath install.log -Encode utf8
```

2. Click Yes to proceed if you see any user prompt messages.


## Change the path environment variables (Advanced)
