# Quick launch of jupyter notebook
$conda_path=Join-Path $env:USERPROFILE "Anaconda3"
$conda_bin=Join-Path "$conda_path" "Library\bin"
$conda_scripts=Join-Path "$conda_path" "Scripts"
$Env:Path += ";$conda_bin"
$Env:Path += ";$conda_scripts"

#Somehow we should set path variable in order to launch python in miniconda3 directory
$Env:Path += ";$conda_path"

$solcorePath=".\solcore5-master"
$logFile="diag_log.txt"

conda list | Out-File -FilePath $logFile
pip list | Out-File -FilePath $logFile -Append

if (!(Test-Path $solcorePath))
{
  Write-Output "solcore5 path not found" | Out-File -FilePath $logFile -Append
}
else{
  Get-ChildItem -Path $solcorePath -Recurse | Out-File -FilePath $logFile -Append
}
