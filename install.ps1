# TODO:check the latest version of this script and update it

Function Get-FolderName($initialDirectory)
{
 [System.Reflection.Assembly]::LoadWithPartialName("System.windows.forms") |
 Out-Null

 $OpenFileDialog = New-Object System.Windows.Forms.FolderBrowserDialog
 $OpenFileDialog.ShowDialog() | Out-Null
 return $OpenFileDialog.SelectedPath
} #end function Get-FileName

$initPath=Get-Location
Write-Host "Please select a directory to install the software..."
$this_path=Get-FolderName -initialDirectory $initPath

#$this_path=Get-Location
#$conda_path=Join-Path $env:USERPROFILE "Miniconda3"
$conda_path=Join-Path -Path "$this_path" -ChildPath "Miniconda3"
$conda_bin=Join-Path "$conda_path" "Library\bin"
$conda_scripts=Join-Path "$conda_path" "Scripts"
$Env:Path += ";$conda_bin"
$Env:Path += ";$conda_scripts"

#Somehow we should set path variable in order to launch python in miniconda3 directory
$Env:Path += ";$conda_path"

#download Miniconda
# The installation instruction is from https://conda.io/docs/user-guide/install/windows.html#install-win-silent
Write-Host "Check if Miniconda3.exe is downloaded....."
if (!(Test-Path "$this_path\Miniconda3.exe"))
{
  Write-Host "Downloading Miniconda3..."
    $miniconda_link="https://repo.continuum.io/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    Invoke-WebRequest -Uri $miniconda_link -OutFile "$this_path\Miniconda3.exe"
}


if (!(Test-Path $conda_path))
{
  #Execute the downloaded file in silent mode
  Write-Host "Installing Miniconda3..."
  $install_conda="start /wait "" Miniconda3.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\Miniconda3"
  CMD /C "$this_path\Miniconda3.exe /InstallationType=JustMe /RegisterPython=0 /S /D=$conda_path"
}
else{

  Write-Host "$conda_path already exists"
}


# download ngspice.
$client = new-object System.Net.WebClient
$ngspice_link= "https://s3-ap-northeast-1.amazonaws.com/kh-deep-learning-model/ngspice-28_64.zip"
Write-Host "Downloading ngspice..."
$client.DownloadFile($ngspice_link,"$this_path\ngspice-28_64.zip")
Write-Host "Extracting ngspice..."
Expand-Archive -LiteralPath "$this_path\ngspice-28_64.zip" -DestinationPath $this_path -Force


# install required python package
conda install --yes numpy scipy matplotlib jupyter cython scikit-image
# Download the masters zip archive. This will also donload the required zip files
$solcore_link="https://github.com/kanhua/solcore5/archive/master.zip"
pip download --no-deps $solcore_link

#$client.DownloadFile($solcore_link,"$this_path\master.zip")

# expand the downlaoded zip
Expand-Archive -LiteralPath master.zip -DestinationPath $this_path -Force

pip install --upgrade -e (Join-Path "$this_path" "solcore5-master")
#configure ngspice in solcore5.


$ngspice_path="$this_path\ngspice-28_64\Spice64\bin\ngspice.exe"

# This python script uses built-in solcore config to rewrite the config file in
# $env:USERPROFILE\.solcore_config.txt
$python_path = "$conda_path\python.exe"
#python setup_spice.py $ngspice_path
Invoke-Expression "$python_path setup_spice.py $ngspice_path"
