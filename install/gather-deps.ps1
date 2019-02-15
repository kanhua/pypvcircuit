Invoke-Expression (Join-Path $PSScriptRoot load-condaenv.ps1)

# this script prepares software for offline install
$pip_command="pip download --dest .\deps pint msgpack"

Invoke-Expression $pip_command
Compress-Archive -Path .\deps -DestinationPath deps.zip