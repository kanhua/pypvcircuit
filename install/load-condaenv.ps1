# Quick launch of jupyter notebook
$conda_path=Join-Path $env:USERPROFILE "Anaconda3"
$conda_bin=Join-Path "$conda_path" "Library\bin"
$conda_scripts=Join-Path "$conda_path" "Scripts"
$Env:Path += ";$conda_bin"
$Env:Path += ";$conda_scripts"

#Somehow we should set path variable in order to launch python in miniconda3 directory
$Env:Path += ";$conda_path"
