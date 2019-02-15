# Install by Powershell

Some PowerShell scripts were prepared to help install and maintain the package.
Please read the scripts before you execute them. Use with your own risk.


## Recommended file structure

```
- YourWorkFolder
  |- install-offline.ps1
  |- install-mainprogram.ps1
  |- Spice64
  |- YourOwnDataFolder
  |- pypvcircuit-master
```

Do not put any data into ```pypvcircuit-master``` folder, 
because the automated software updating script may overwrite any file you created.


## Install Anaconda and ngspice

Installation of this software suite will not require the authorization of administrator of the OS.


## Install pypvcell and other dependent python packages

Run ```install-offline.ps1``` to install the pre-downloaded python dependencies, including pypvcell.
 
## Maintain and update the package

Use ```install-mainprogram.ps1```. This script downloads the latest clone of pypvcircuit, 
extract and overwrite the existing ```pypvcircuit-master``` folder.


## Launch the program

- Run ```load-condaenv.ps1``` if you would like to launch python command from PowerShell.
- Run ```run-jupyter.ps1``` if you would like to launch jupyter notebook files.