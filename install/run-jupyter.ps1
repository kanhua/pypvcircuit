Invoke-Expression (Join-Path $PSScriptRoot load-condaenv.ps1)

Write-Output "Launching jupyter notebook...."
jupyter notebook --notebok-dir="./"
