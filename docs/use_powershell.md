# Enabling PowerShell in you Windows environment

Some powershell scripts are prepared along side with this software for facilitating some daily operations.
Here's how to setup the environment of PowerShell.

### Step 1: Install the latest version of Powershell

Follow [this instruction](https://docs.microsoft.com/en-us/powershell/scripting/setup/installing-windows-powershell?view=powershell-6#upgrading-existing-windows-powershell) to upgrade your Microsoft Powershell to the latest version (PS5.1).
This is done by downloading and installing [Windows Management Framework 5.1](https://docs.microsoft.com/en-us/powershell/scripting/setup/installing-windows-powershell?view=powershell-6#upgrading-existing-windows-powershell).
[This page](https://docs.microsoft.com/en-gb/powershell/wmf/5.1/install-configure#download-and-install-the-wmf-51-package) which file you should download.


### Step 2: Change ExecutionPolicy setting

Reason for this step: by default, Powershell does not allow the execution of third-party powershell script.
We therefore have to allow it to do that temporarily.

1. Run Windows Powershell as administrator. [This page](https://msdn.microsoft.com/en-us/library/dn568022.aspx) shows how to do this.
2. Open Powershell, in the Powershell command line, run the following script

```
> Set-ExecutionPolicy Unrestricted
```

### Step 3: Run the installation script

1. Right click ```install.ps1```, select **Run with Powershell**.

2. Click Yes to proceed if you see any user prompt messages.

Note: All the software will be downloaded in the same directory of ```install.ps1```

#### Run ```install.ps1``` from terminal

1. In file explorer, go to the folder of ```solar-cell-circuit-master```   
![folder](./doc_images/to_folder.png)

2. Click File -> Open Windows Powershell   
![open_powershell](./doc_images/open_powershell.png)

3. In powershell, type ```.\install.ps1```   
![in_powershell](./doc_images/in_powershell.png)


### Step 4: Change ExecutionPolicy setting back

For security, we switch the execution policy back.
1. Run Windows Powershell as administrator. [This page](https://msdn.microsoft.com/en-us/library/dn568022.aspx) shows how to do this.
2. Open Powershell, in the Powershell command line, run the following script

```
> Set-ExecutionPolicy restricted
```


