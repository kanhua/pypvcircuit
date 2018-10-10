# TODO:check the latest version of this script and update it

Function Check-CondaFileExists($FilePath, $ExpectedFileHash)
{
  if (!(Test-Path $FilePath))
  {
    return $false
  }
  else
  {
    $fileHash=(Get-FileHash -Path $FilePath -algorithm MD5).Hash
    if ($fileHash -eq $ExpectedFileHash)
    { return $true }
    else { return $false }
  }

}


$this_path=$PSScriptRoot
Write-Output "The software files will be downloaded to: $this_path"
$conda_path=Join-Path $env:USERPROFILE "Anaconda3"
Write-Output "Anaconda will be installed in $conda_path"
$conda_bin=Join-Path "$conda_path" "Library\bin"
$conda_scripts=Join-Path "$conda_path" "Scripts"
$Env:Path += ";$conda_bin"
$Env:Path += ";$conda_scripts"

#Somehow we should set path variable in order to launch python in miniconda3 directory
$Env:Path += ";$conda_path"

$condaFileHash="82ED9D1D93AB2EA6A605B4DA3B2D35A9"
#download Miniconda
# The installation instruction is from https://conda.io/docs/user-guide/install/windows.html#install-win-silent
Write-Host "Check if Anaconda3.exe is downloaded....."
if (!(Check-CondaFileExists -FilePath "$this_path\Anaconda3.zip" -ExpectedFileHash $condaFileHash))
{
  Write-Host "Downloading Anaconda3..."
    $miniconda_link="https://repo.continuum.io/archive/.winzip/Anaconda3-5.2.0-Windows-x86_64.zip"
    Invoke-WebRequest -Uri $miniconda_link -OutFile "$this_path\Anaconda3.zip"
    Expand-Archive -LiteralPath "$this_path\Anaconda3.zip" -DestinationPath $this_path -Force
}


if (!(Test-Path $conda_path))
{
  #Execute the downloaded file in silent mode
  Write-Output "Installing Anaconda3, this may take a few minutes....."
  CMD /C "$this_path\shared\www\archive\Anaconda3-5.2.0-Windows-x86_64.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%UserProfile%\Anaconda3"
  if (Test-Path $conda_path)
  {
    Write-Output "Anaconda3 is installed."
  }
}
else{

  Write-Output "$conda_path already installed"
}


# download ngspice.
$client = new-object System.Net.WebClient
$ngspice_link= "https://s3-ap-northeast-1.amazonaws.com/kh-deep-learning-model/s_ngspice-28_64.zip"
$ngspiceHash="393D5E2924704B7C202B31B6BF6B88A2"

$ngspiceZipPath="$this_path\ngspice-28_64.zip"

if (!(Check-CondaFileExists -FilePath $ngspiceZipPath -ExpectedFileHash $ngspiceHash))
{
  Write-Output "Downloading ngspice..."
  $client.DownloadFile($ngspice_link, $ngspiceZipPath)
}
else
{
  Write-Output "ngspice has been downloaded..."
}

Write-Output "Extracting ngspice..."
Expand-Archive -LiteralPath "$this_path\ngspice-28_64.zip" -DestinationPath $this_path -Force


# install required python package
# conda install --yes numpy scipy matplotlib jupyter cython scikit-image
# Download the masters zip archive. This will also donload the required zip files
Write-Output "Downloading Solcore5....."

$solcore_link="https://s3-ap-northeast-1.amazonaws.com/kh-deep-learning-model/s_solcore5-master.zip"
$client.DownloadFile($solcore_link, "$this_path\master.zip")

Write-Output "Extracting Solcore5....."
Expand-Archive -LiteralPath master.zip -DestinationPath $this_path -Force


Write-Output "Downloading dependencies of Solcore5....."
$solcoreDepsLink="https://s3-ap-northeast-1.amazonaws.com/kh-deep-learning-model/s_solcore_deps.zip"
$client.DownloadFile($solcoreDepsLink, "$this_path\solcore_deps.zip")
Expand-Archive -LiteralPath "$this_path\solcore_deps.zip" -DestinationPath $this_path -Force

Write-Output "Installing Solcore5...."
pip install --no-index --find-links .\deps -e (Join-Path "$this_path" "solcore5-master")

#configure ngspice in solcore5.

$ngspice_path="$this_path\Spice64\bin\ngspice.exe"

# This python script uses built-in solcore config to rewrite the config file in
# $env:USERPROFILE\.solcore_config.txt

Write-Output "Configuring solcore5...."
$python_path = "$conda_path\python.exe"
#python setup_spice.py $ngspice_path
Invoke-Expression "$python_path setup_spice.py $ngspice_path"

Write-Output "Install completed"
