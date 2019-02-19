<#
.description
This script pre-downloads python packages for later offline installation, namely install-offline.ps1

#>
Invoke-Expression (Join-Path $PSScriptRoot load-condaenv.ps1)

# this script prepares software for offline install
$pip_command="pip download --dest .\deps pint msgpack"

Invoke-Expression $pip_command
Compress-Archive -Path .\deps -DestinationPath deps.zip