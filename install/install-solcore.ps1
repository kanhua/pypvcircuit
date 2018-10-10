# Quick launch of jupyter notebook
$conda_path=Join-Path $env:USERPROFILE "Anaconda3"
$conda_bin=Join-Path "$conda_path" "Library\bin"
$conda_scripts=Join-Path "$conda_path" "Scripts"
$Env:Path += ";$conda_bin"
$Env:Path += ";$conda_scripts"

#Somehow we should set path variable in order to launch python in miniconda3 directory
$Env:Path += ";$conda_path"

$this_path=$PSScriptRoot
$logFile="solcore_install_log.txt"

Write-Output "Installing Solcore5...."
#pip install --no-index --find-links .\deps -e (Join-Path "$this_path" "solcore5-master") | Out-File -FilePath $logFile
$solcorePath=Join-Path "$this_path" "solcore5-master"
$pipOutput=(pip install --no-index --find-links .\deps -e $solcorePath) 2>&1
Write-Output $pipOutput | Out-File -FilePath $logFile

$ngspice_path="$this_path\Spice64\bin\ngspice.exe"

# This python script uses built-in solcore config to rewrite the config file in
# $env:USERPROFILE\.solcore_config.txt

Write-Output "Configuring solcore5...."
$python_path = "$conda_path\python.exe"
#python setup_spice.py $ngspice_path
$setupOutput=(Invoke-Expression "$python_path setup_spice.py $ngspice_path") 2>&1

Write-Output $setupOutput | Out-File -FilePath $logFile -Append
Write-Output "Script completed"
