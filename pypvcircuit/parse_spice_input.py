import networkx
import re


def parse_spice_command(command: str):
    floating_point_num_pat = "[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?"

    r_pat = '(?P<name>[Rr]\w+)\s+(?P<pnode>\w+)\s+(?P<nnode>\w+)\s+(?P<value>[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)'

    i_pat = '(?P<name>[Ii]\w+)\s+(?P<pnode>\w+)\s+(?P<nnode>\w+)\s+(?P<value>[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)'

    v_pat = '(?P<name>[Vv]\w+)\s+(?P<pnode>\w+)\s+(?P<nnode>\w+)\s+DC\s+(?P<value>[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)'

    d_pat = '(?P<name>[Dd]\w+)\s+(?P<pnode>\w+)\s+(?P<nnode>\w+)\s+(?P<value>\w+)'

    pattern_base = dict()

    pattern_base['v'] = v_pat
    pattern_base['r'] = r_pat
    pattern_base['d'] = d_pat
    pattern_base['i'] = i_pat

    cmd_atoms = dict()

    try:
        match_obj = re.match(pattern_base[command[0].lower()], command)
    except ValueError:
        print("The input command is not valid")
        return None

    if match_obj is not None:
        cmd_atoms['name'] = match_obj['name']
        cmd_atoms['p_node'] = match_obj['pnode']
        cmd_atoms['n_node'] = match_obj['nnode']
        cmd_atoms['value'] = match_obj['value']
        if command[0].lower() in ['v', 'r', 'i']:
            cmd_atoms['value'] = float(cmd_atoms['value'])

    return cmd_atoms


def parse_v_probe(command: str):
    cmd_atoms = dict()
    pat = ".PRINT DC v\((?P<node1>\w+)\) v\((?P<node2>\w+)\)"

    match_obj = re.match(pat, command)

    if match_obj is not None:
        cmd_atoms['p_node'] = match_obj['node1']
        cmd_atoms['n_node'] = match_obj['node2']

    else:
        cmd_atoms = None

    return cmd_atoms


def is_device(command: str):
    command = command.lstrip()
    if len(command) == 0:
        return False

    # Find the lines that describes a deivce
    # TODO: this line should be more general
    # for now we only assume we only have reisitors (r),
    # diodes (d), voltage (v) and current (i) sources
    if command[0] in ['R', 'r', 'V', 'd', 'i', 'v']:
        return True
    else:
        return False


def add_rep_node(circuit_graph: networkx.Graph)->networkx.Graph:
    """
    Find the root of a node and record it to
    ```circuit_graph.nodes[node]['root'] = node_root```

    :param circuit_graph: the graph that represents the circuit
    :return: processed circuit graph
    """

    shorted_set = list(networkx.connected_components(circuit_graph))

    # Every node will have an attribute 'root', every "shorted nodes"
    # in the circuit will be given the new name 'root'

    set_id = 1
    for cset in shorted_set:

        # '0' is earth in SPICE. Any nodes shorted to '0' should be '0'
        if '0' in cset:
            node_root = '0'

        # otherwise we give the nodes another name.
        else:
            node_root = 'sn{}'.format(set_id)
            set_id += 1

        for node in cset:
            circuit_graph.nodes[node]['root'] = node_root

    return circuit_graph


class NodeReducer(object):

    def __init__(self):

        self.shorted_node_g = networkx.Graph()

    def find_root(self, node):

        return self.shorted_node_g.nodes[node]['root']

    def process_spice_input(self, spice_input_contents: str):
        """
        Find the commands in the SPICE input string that has zero resistance.


        :param spice_input_contents:
        :return:
        """
        commands = spice_input_contents.splitlines()

        new_commands = []

        reprocessed_output = ""

        # Read the input and construct the netwrok graph
        for c in commands:
            if len(c) == 0:
                continue

            if c[0] in ['R', 'r']:
                r_cmd = parse_spice_command(c)
                if r_cmd['value'] == 0:

                    # we should add nodes first. Otherwise we cannot assign
                    # the attributes of the nodes later
                    self.shorted_node_g.add_nodes_from([r_cmd['p_node'], r_cmd['n_node']])

                    self.shorted_node_g.add_edge(r_cmd['p_node'], r_cmd['n_node'])
                else:
                    # resistors that are shorted will be discarded
                    new_commands.append(c)
            else:
                new_commands.append(c)

        shorted_node_g = add_rep_node(self.shorted_node_g)

        # write the processed spice commands
        for c in new_commands:
            c = c.lstrip()
            if len(c) == 0:
                continue

            if is_device(c):
                dev_cmd = parse_spice_command(c)

                if len(dev_cmd.keys()) == 0:
                    print("Error of parsing {}".format(c))


                u = dev_cmd['p_node']
                v = dev_cmd['n_node']
                if u in shorted_node_g:
                    dev_cmd['p_node'] = shorted_node_g.nodes[u]['root']

                if v in shorted_node_g:
                    dev_cmd['n_node'] = shorted_node_g.nodes[v]['root']

                new_cmd_str = "{name} {p_node} {n_node} {value}".format(**dev_cmd)

                reprocessed_output += (new_cmd_str + "\n")

            elif parse_v_probe(c) is not None:

                dev_cmd = parse_v_probe(c)

                u = dev_cmd['p_node']
                v = dev_cmd['n_node']

                if u in shorted_node_g:
                    dev_cmd['p_node'] = shorted_node_g.nodes[u]['root']

                if v in shorted_node_g:
                    dev_cmd['n_node'] = shorted_node_g.nodes[v]['root']

                if dev_cmd['n_node'] == '0':
                    new_cmd_str = ".PRINT DC v({p_node})".format(**dev_cmd)
                else:

                    new_cmd_str = ".PRINT DC v({p_node}) v({n_node})".format(**dev_cmd)

                reprocessed_output += (new_cmd_str + "\n")

            else:
                reprocessed_output += (c + "\n")

        return reprocessed_output


def reprocess_spice_input(spice_input_content: str):
    nd = NodeReducer()

    return nd.process_spice_input(spice_input_content)


if __name__ == "__main__":
    test_file = "/Users/kanhua/Dropbox/Programming/solar-cell-circuit/spice_in.txt"
    with open(test_file, 'r') as fp:
        contents = fp.read()

    output_str = reprocess_spice_input(contents)
    print(output_str)
