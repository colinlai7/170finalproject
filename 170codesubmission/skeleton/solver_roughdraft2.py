import networkx as nx
import os
from subprocess import call

###########################################
# Change this variable to the path to 
# the folder containing all three input
# size category folders
###########################################
path_to_inputs = "./all_inputs" # change between inputs and all_inputs

###########################################
# Change this variable if you want
# your outputs to be put in a 
# different folder
###########################################
path_to_outputs = "./outputs"

def parse_input(folder_name):
    '''
        Parses an input and returns the corresponding graph and parameters

        Inputs:
            folder_name - a string representing the path to the input folder

        Outputs:
            (graph, num_buses, size_bus, constraints)
            graph - the graph as a NetworkX object
            num_buses - an integer representing the number of buses you can allocate to
            size_buses - an integer representing the number of students that can fit on a bus
            constraints - a list where each element is a list vertices which represents a single rowdy group
    '''
    graph = nx.read_gml(folder_name + "/graph.gml")
    graph.remove_edges_from(graph.selfloop_edges())
    edgelist = list(graph.edges)
    nodelist = list(graph.nodes)
    # because hmetis needs 1-based numbering
    #TODO: REMEMBER TO EDIT string_incrementer into a more robust mapping between provided node labels
    #  and natural numbers (excluding 0)
    def string_incrementer(list_of_lists):
        for i in range(len(list_of_lists)):
            list_of_lists[i] = [str(nodelist.index(list_of_lists[i][j]) + 1) for j in range(len(list_of_lists[i]))]
    string_incrementer(edgelist)
    parameters = open(folder_name + "/parameters.txt")
    num_buses = int(parameters.readline())
    size_bus = int(parameters.readline())
    constraints = []

    # Now I am building the hmetis input file.  I gain info needed first, then write at once
    # note that this goes through parameters/constraints twice instead of once and is a bit slower
    #   The structure is as follows:
    #   first line contains num_hyperedges num_vertices fmt=1
    #   Following group of lines is rowdy groups
    #   Last group of lines is the normal edges as hyperedges

    for line in parameters:
        line = line[1: -2]
        curr_constraint = [num.replace("'", "") for num in line.split(", ")]
        # if len(curr_constraint) == 1:
        #     continue
        constraints.append(curr_constraint)

    # again because hmetis needs 1 based numbering
    string_incrementer(constraints)

    num_hyperedges = len(edgelist) + len(constraints)
    num_vertices = nx.number_of_nodes(graph)
    hmetis_input = open(folder_name + "/hmetis_input.graph", "w")
    hmetis_input.write(str(num_hyperedges) + " " + str(num_vertices) + " 1\n")
    for rowdy_group in constraints:
        hmetis_input.write("1 " + ' '.join(rowdy_group) + "\n")
    for edge in edgelist:
        hmetis_input.write("10 " + ' '.join(edge) + "\n")
        # by editing the weight of the hyperedge of real friendships, we can adjust how easily they are broken
    hmetis_input.close()
    return folder_name + "/hmetis_input.graph", num_buses, size_bus, folder_name, nodelist
    # return graph, num_buses, size_bus, constraints

def solve(hmetis_input_path, num_buses, size_bus, hmetis_output_path):
    #TODO: Write this method as you like. We'd recommend changing the arguments here as well
    if num_buses < 2:
        hmetis_input_graph = open(hmetis_input_path)
        firstline = hmetis_input_graph.readline()
        second_num = int(firstline.split(" ")[1])
        hmetis_output_partitions = open(hmetis_output_path + "/hmetis_input.graph.part.1", "w")
        for i in range(second_num):
            hmetis_output_partitions.write("0\n")
        return
    numparts = str(num_buses)
    ubfactor = "6"
    nruns = "1"
    ctype = "1"
    # rtype or otype is hmetis vs khmetis specific
    vcycle = "1"

    if num_buses <= 16:
        # want to use hmetis
        rtype = "1"
        reconst = "1"
        dbglvl = "0"
        call(['./hmetis-1.5-linux/hmetis', hmetis_input_path, numparts, ubfactor, nruns, ctype, rtype, vcycle, reconst, dbglvl])
    else:
        # want to use khmetis
        otype = "1"
        dbglvl = "0"
        call(['./hmetis-1.5-linux/khmetis', hmetis_input_path, numparts, ubfactor, nruns, ctype, otype, vcycle, dbglvl])
    try:
        open(hmetis_input_path + ".part." + str(num_buses))
    except FileNotFoundError:
        rtype = "1"
        reconst = "1"
        dbglvl = "0"
        call(['./hmetis-1.5-linux/hmetis', hmetis_input_path, numparts, ubfactor, nruns, ctype, rtype, vcycle, reconst, dbglvl])

def main():
    '''
        Main method which iterates over all inputs and calls `solve` on each.
        The student should modify `solve` to return their solution and modify
        the portion which writes it to a file to make sure their output is
        formatted correctly.
    '''
    size_categories = ["small", "medium", "large"] # removed large
    if not os.path.isdir(path_to_outputs):
        os.mkdir(path_to_outputs)

    for size in size_categories:
        category_path = path_to_inputs + "/" + size
        output_category_path = path_to_outputs + "/" + size
        category_dir = os.fsencode(category_path)
        
        if not os.path.isdir(output_category_path):
            os.mkdir(output_category_path)

        for input_folder in os.listdir(category_dir):
            print(input_folder)
            if input_folder == b"1009":
                continue
            input_name = os.fsdecode(input_folder)
            hmetis_input_path, num_buses, size_bus, hmetis_output_path, nodelist = parse_input(category_path + "/" + input_name)
            solve(hmetis_input_path, num_buses, size_bus, hmetis_output_path)

            output_file = open(output_category_path + "/" + input_name + ".out", "w")
            #
            # #TODO: modify this to write your solution to your
            # #      file properly as it might not be correct to
            # #      just write the variable solution to a file
            #
            # # need to use hmetis_output_path in order to read the hmetis output file, parse it, and
            # # produce a viable cs170 scorable output.  Remember to start counting from 0 for the outputs,
            # # because all the node labels were artificially incremented in the input parser, whereas they
            # # don't need to be and shouldn't be artificially incremented in the output parser.
            current_node = 0
            partitionmap = {i:[] for i in range(num_buses)}
            partitions = open(hmetis_input_path + ".part." + str(num_buses))
            for line in partitions:
                line = int(line)
                # this turns the partition number into an integer type
                partitionmap[line].append(nodelist[current_node])
                current_node += 1
            for partition in partitionmap.keys():
                output_file.write("{}\n".format(partitionmap[partition]))

            # #####
            output_file.close()

if __name__ == '__main__':
    main()


