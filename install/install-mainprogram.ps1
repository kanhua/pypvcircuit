$this_path=$PSScriptRoot
Write-Output $this_path
$conda_path=$conda_path=Join-Path $env:USERPROFILE "Anaconda3"
Invoke-WebRequest -Uri https://github.com/kanhua/solar-cell-circuit/archive/master.zip -OutFile solar-cell-circuit.zip

Write-Output "Extracting Dependencies....."
Expand-Archive -LiteralPath solar-cell-circuit.zip -DestinationPath $this_path -Force

$ngspice_path="$this_path\Spice64\bin\ngspice.exe"
$output_path="$this_path\output"


Write-Output "Configuring pypvcircuit and ngspice...."
$python_path = "$conda_path\python.exe"
Invoke-Expression "$python_path solar-cell-circuit-master\setup_spice.py $ngspice_path $output_path"

Write-Output "Install completed"