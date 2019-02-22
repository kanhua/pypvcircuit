$this_path=$PSScriptRoot
Invoke-Expression "$PSScriptRoot\load-condaenv.ps1"
$conda_path=$conda_path=Join-Path $env:USERPROFILE "Anaconda3"
$client = new-object System.Net.WebClient

Write-Output "Downloading required packages"

$deps_link="https://s3-ap-northeast-1.amazonaws.com/kanhua-share/deps.zip"
$client.DownloadFile($deps_link, "$this_path\master.zip")

Write-Output "Extracting Dependencies....."
Expand-Archive -LiteralPath deps.zip -DestinationPath $this_path -Force

Write-Output "Downloading Pypvcell..."

Expand-Archive -LiteralPath pypvcell.zip -DestinationPath $this_path -Force
$client.DownloadFile("https://s3-ap-northeast-1.amazonaws.com/kanhua-share/pypvcell-master.zip", "$this_path\pypvcell.zip")
pip install --no-index --find-links .\deps pint msgpack

Write-Output "Installing Pypvcell...."
pip install --no-index --find-links .\deps -e .\pypvcell-master\

Invoke-Expression (Join-Path $PSScriptRoot .\install-mainprogram.ps1) 

Write-Output "Install completed"