import re
import numpy as np

def parse_output(raw_results: str):
    result = dict()

    lines = raw_results.split("\n")

    header_pat = "Index\s+v-sweep\s+v(\S+)"

    find_data_row_pat = "No.\s+of\s+Data\s+Rows\s*:\s*([\d]+)"

    floating_number_pat = "[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?"

    data_pat = "\d+\s+" + floating_number_pat + "\s+" + floating_number_pat

    data_num = 0
    V = np.empty(data_num)
    I = np.empty(data_num)

    found_row_num = False
    aq_flag = False
    v_name = "null"

    for line in lines:

        if not found_row_num:
            matched_obj = re.match(find_data_row_pat, line)
            if matched_obj:
                # print("number of data:{}".format(matched_obj[1]))

                data_num = int(matched_obj[1])
                found_row_num = True
                V = np.empty(data_num)
                I = np.empty(data_num)
        else:

            # start acquire data
            if aq_flag:
                if re.match(data_pat, line):

                    data_list = line.split()

                    V[int(data_list[0])] = float(data_list[1])
                    I[int(data_list[0])] = float(data_list[2])

                    if int(data_list[0]) == data_num - 1:
                        aq_flag = False
                        result[v_name] = (V.copy(), I.copy())

            else:
                matched_obj = re.match(header_pat, line)
                if matched_obj:
                    v_name = matched_obj[1]
                    aq_flag = True
                    continue

    return result