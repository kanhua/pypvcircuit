"""
Solves an electrical circuit using SPICE. The input must be a correctly formated SPICE file and the output will be
the raw result from SPICE or after some processing, depending of what is requested.
The code is adapted from solcore5 (https://github.com/dalonsoa/solcore5)

"""

import numpy
import os
import subprocess
import tempfile
from .parse_spice_input import reprocess_spice_input
from .config_tool import user_config_data


class SpiceConfig:
    engine = user_config_data.get('External programs', 'spice')
    input_file = "current_spice.cir"
    output_file = "current_spice.out"


def solve_circuit(spice_file_contents, engine=SpiceConfig.engine, raw=True, postprocess_input=reprocess_spice_input):
    """
    Sends the spice-readable file to the spice engine which will run it and store the data in a temporary folder.
    Once the process is finished, it collects the data and returns it.

    If raw=False, this function will return only lines that start with a number. Depending of what was the output,
    the result might make sense or not. It is safer to ask for the raw data as it allows you to collect all the output
    from spice and deal with it as convenient, depending on the application.

    :param spice_file_contents: string formated as a spice-readable file contaning the design of the circuit and the instructions
    :param engine: the spice engine.
    :param raw: whether to produce the raw output or after some processing.
    :return: depending of the value of raw, this might be all the output of spice or just an array of data
    """

    SpiceConfig.engine = engine

    with open("spice_in_raw.txt", "w") as f:
        f.write(spice_file_contents)

    # post process the input script if necessary
    if postprocess_input is not None:
        spice_file_contents = postprocess_input(spice_file_contents)

    with tempfile.TemporaryDirectory(prefix="tmp", suffix="_sc3NGSPICE") as working_directory:

        spice_file_path = os.path.join(working_directory, SpiceConfig.input_file)
        spice_output_path = os.path.join(working_directory, SpiceConfig.output_file)

        with open(spice_file_path, "w") as f:
            f.write(spice_file_contents)

        with open("spice_in.txt", "w") as f:
            f.write(spice_file_contents)

        this_process = subprocess.Popen([SpiceConfig.engine, '-b', spice_file_path, '-o', spice_output_path])
        this_process.wait()

        # this_process = subprocess.run([spice.engine, '-b', spice_file_path, '-o', spice_output_path])
        with open(spice_output_path, "r") as f:
            raw_results = f.read()

        with open("spice_out.txt", "w") as f:
            f.write(raw_results)

        if raw:
            # We return all the output
            return raw_results

        else:
            # We return just the lines starting with a number, which is OK in certain simple cases
            lines = raw_results.split("\n")
            data = []
            for line in lines:
                if len(line) == 0 or line[0] not in "1234567890.":
                    continue
                # print (line)

                i, *rest = line.split()
                # print (len(rest))
                data.append([float(element) for element in rest])

            return numpy.array(data).transpose()


def get_raw_from_spice(spice_file_contents, engine=SpiceConfig):
    """ Dummy function included for backwards compatibility with solcore3 """

    results = solve_circuit(spice_file_contents, engine)

    return results


def send_to_spice(spice_file_contents, engine=SpiceConfig):
    """ Dummy function included for backwards compatibility with solcore3 """

    results = solve_circuit(spice_file_contents, engine, raw=False)

    return results


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    engine = SpiceConfig.engine
    circuit = """Multiple dc sources
v1 1 0
r1 1 0 3.3k
.dc v1 0 24 1
.print dc i(v1)
.end
    """

    data = solve_circuit(circuit, engine=engine, raw=False)
    print(data)

    plt.plot(data[0], data[1])
    plt.show()
