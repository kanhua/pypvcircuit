# How to install Solcore5 and ngspice

## Overview
This script will download and install the following software:

1. [Miniconda](https://conda.io/miniconda.html): A python language distribution made for scientific computing.
2. Solcore5: A solar cell modeling library written in python
3. NGSpice: A circuit network library

All the software will be installed in a folder of your choice.
Installation of this software suite will not require the authorization of administrator of the OS.

## Install the software suite

### Step 1: Install the latest version of Powershell

Follow [this instruction](https://docs.microsoft.com/en-us/powershell/scripting/setup/installing-windows-powershell?view=powershell-6#upgrading-existing-windows-powershell) to upgrade your Microsoft Powershell to the latest version (PS5.1).
This is done by downloading and installing [Windows Management Framework 5.1](https://docs.microsoft.com/en-us/powershell/scripting/setup/installing-windows-powershell?view=powershell-6#upgrading-existing-windows-powershell).
[This page](https://docs.microsoft.com/en-gb/powershell/wmf/5.1/install-configure#download-and-install-the-wmf-51-package) which file you should download. 


### Step 2: Change ExecutionPolicy setting

Reason for this step: by default, Powershell does not allow the execution of third-party powershell script.
We therefore have to allow it to do that temporarily.

1. Run Windows Powershell as administrator. [This page](https://msdn.microsoft.com/en-us/library/dn568022.aspx) shows how to do this.
2. Open Powershell, in the powershell command line, run the following script

```
> Set-ExecutionPolicy Unrestricted
```

### Step 3: Run the installtion script

1. Right click ```install.ps1```, select **Run with Powershell**.

2. Click Yes to proceed if you see any user prompt messages.

Note: All the software will be downloaded in the same directory of ```install.ps1```


### Step 4: Change ExecutionPolicy setting back

For security, we switch the execution policy back.
1. Run Windows Powershell as administrator. [This page](https://msdn.microsoft.com/en-us/library/dn568022.aspx) shows how to do this.
2. Open Powershell, in the powershell command line, run the following script

```
> Set-ExecutionPolicy restricted
```


## Change the path environment variables (Advanced)
