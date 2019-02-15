$this_path=$PSScriptRoot
$conda_path=$conda_path=Join-Path $env:USERPROFILE "Anaconda3"
$client = new-object System.Net.WebClient

Write-Output "Downloading required packages"

#$deps_link="https://s3-ap-northeast-1.amazonaws.com/bucket-name/file-name"
#$client.DownloadFile($deps_link, "$this_path\master.zip")

Write-Output "Extracting Dependencies....."
Expand-Archive -LiteralPath master.zip -DestinationPath $this_path -Force

Write-Output "Installing Pypvcell...."
pip install --no-index --find-links .\deps -e (Join-Path (Join-Path -Path $this_path "deps") "pypvcell-0.1.0\pypvcell")

Write-Output "Updating the main program"
Invoke-WebRequest -Uri https://github.com/kanhua/solar-cell-circuit/archive/master.zip



#configure ngspice in solcore5.

$ngspice_path="$this_path\Spice64\bin\ngspice.exe"
$output_path="$this_path\output"

# This python script uses built-in solcore config to rewrite the config file in
# $env:USERPROFILE\.solcore_config.txt

Write-Output "Configuring pypvcircuit and ngspice...."
$python_path = "$conda_path\python.exe"
Invoke-Expression "$python_path setup_spice.py $ngspice_path $output_path"

Write-Output "Install completed"