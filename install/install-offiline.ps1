$this_path=$PSScriptRoot
$conda_path=$conda_path=Join-Path $env:USERPROFILE "Anaconda3"
$client = new-object System.Net.WebClient

Write-Output "Downloading required packages"

#$deps_link="https://s3-ap-northeast-1.amazonaws.com/bucket-name/file-name"
#$client.DownloadFile($deps_link, "$this_path\master.zip")

Write-Output "Extracting Dependencies....."
Expand-Archive -LiteralPath deps.zip -DestinationPath $this_path -Force

Write-Output "Downloading Pypvcell..."
Invoke-WebRequest -Uri https://github.com/kanhua/pypvcell/archive/master.zip -OutFile pypvcell.zip
Expand-Archive -LiteralPath pypvcell.zip -DestinationPath $this_path -Force

pip install --no-index --find-links .\deps pint msgpack

Write-Output "Installing Pypvcell...."
pip install --no-index --find-links .\deps -e .\pypvcell-master\

Invoke-Expression (Join-Path $PSScriptRoot .\install-mainprogram.ps1) 

Write-Output "Install completed"