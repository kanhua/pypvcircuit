import copy
import networkx


def parse_spice_command(command: str):
    name, p_node, n_node, value = command.split()

    cmd_atoms = dict()
    cmd_atoms['name'] = name
    cmd_atoms['p_node'] = p_node
    cmd_atoms['n_node'] = n_node
    if command[0] != 'd':
        cmd_atoms['value'] = float(value)
    else:
        cmd_atoms['value'] = value

    return cmd_atoms


def is_device(command: str):
    command = command.lstrip()
    if len(command) == 0:
        return False

    if command[0] in ['R', 'r', 'V', 'd', 'i']:
        return True
    else:
        return False


def add_rep_node(circuit_graph):
    shorted_set = list(networkx.connected_components(circuit_graph))

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


def reprocess_spice_input(contents: str):


    commands = contents.splitlines()

    shorted_node_g = networkx.Graph()

    new_commands=[]

    reprocessed_output=""

    for c in commands:
        if len(c) == 0:
            continue

        if c[0] in ['R', 'r']:
            r_cmd = parse_spice_command(c)
            if r_cmd['value'] == 0:
                shorted_node_g.add_nodes_from([r_cmd['p_node'], r_cmd['n_node']])
                shorted_node_g.add_edge(r_cmd['p_node'], r_cmd['n_node'])
            else:
                # resistors that are shorted will be discarded
                new_commands.append(c)
        else:
            new_commands.append(c)


    shorted_node_g = add_rep_node(shorted_node_g)

    for c in new_commands:
        c = c.lstrip()
        if len(c) == 0:
            continue

        if is_device(c):
            dev_cmd = parse_spice_command(c)
            u = dev_cmd['p_node']
            v = dev_cmd['n_node']
            if u in shorted_node_g:
                dev_cmd['p_node'] = shorted_node_g.nodes[u]['root']

            if v in shorted_node_g:
                dev_cmd['n_node'] = shorted_node_g.nodes[v]['root']

            new_cmd_str = "{name} {p_node} {n_node} {value}".format(**dev_cmd)

            reprocessed_output+=(new_cmd_str+"\n")

        else:
            reprocessed_output+=(c+"\n")


    return reprocessed_output


if __name__ == "__main__":
    test_file = "/Users/kanhua/Dropbox/Programming/solar-cell-circuit/spice_in.txt"
    with open(test_file, 'r') as fp:
        contents = fp.read()


    output_str=reprocess_spice_input(contents)
    print(output_str)
