from spice import solve_circuit

spice_in_path = "/Users/kanhua/Dropbox/Programming/solar-cell-circuit/spice/spice_in_fix.txt"

with open(spice_in_path, "r") as f:
    spice_contents = f.read()

solve_circuit(spice_contents)
