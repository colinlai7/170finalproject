import networkx as nx
import os
from subprocess import call
from multiprocessing import Pool
from asdf import score_output
import random
from shutil import copyfile
from copy import deepcopy

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
    graph.remove_edges_from(graph.selfloop_edges()) # not sure if this line is necessary or beneficial
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

def solve(hmetis_input_path, num_buses, size_bus, hmetis_output_path, nodelist, category_path, input_name, output_category_path):
    def parse_output():
        output_file = open(output_category_path + "/" + input_name + ".out", "w")
        current_node = 0
        partitionmap = {i: [] for i in range(num_buses)}
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
    def check_bus_overfill():
        score, message = score_output(category_path + "/" + input_name, output_category_path + "/" + input_name + ".out")
        if message.split(" ")[-1] == "capacity":
            return True
        else:
            return False
    def manual_bus_stalin_relocation():
        input_folder = category_path + "/" + input_name
        output_file = output_category_path + "/" + input_name + ".out"

        # graph = nx.read_gml(input_folder + "/graph.gml")
        parameters = open(input_folder + "/parameters.txt")
        num_buses = int(parameters.readline())
        size_bus = int(parameters.readline())
        # constraints = []
        #
        # for line in parameters:
        #     line = line[1: -2]
        #     curr_constraint = [node.replace("'", "") for node in line.split(", ")]
        #     constraints.append(curr_constraint)

        output = open(output_file)
        assignments = []
        for line in output:
            line = line[1: -2]
            curr_assignment = [node.replace("'", "") for node in line.split(", ")]
            assignments.append(curr_assignment)

        overfilled_buses = {} # map a bus number to how many overflow students
        buses_with_space = {} # map a bus number to how much space there is
        for i in range(len(assignments)):
            if len(assignments[i]) > size_bus:
                overfilled_buses[i] = len(assignments[i]) - size_bus
            if len(assignments[i]) <= 0:
                buses_with_space[i] = size_bus
            if len(assignments[i]) < size_bus:
                buses_with_space[i] = size_bus - len(assignments[i])

        def random_replacement_attempt(i):
            assignmentscopy = deepcopy(assignments)
            lucky_peasants_to_be_relocated = []
            buses_with_relocated_peasants = {}

            # keeping track of all the overflow peasants
            for bus_num, overflow_num in overfilled_buses.items():
                peasants_kicked_from_this_bus = random.sample(assignmentscopy[bus_num], overflow_num)
                lucky_peasants_to_be_relocated.extend(peasants_kicked_from_this_bus)
                # Deleting the relocated peasants from old bus when they are moved to a new bus
                for peasant in peasants_kicked_from_this_bus:
                    assignmentscopy[bus_num].remove(peasant)

            # keeping track of the new bus assignments for the overflow peasants
            for bus_num, space in buses_with_space.items():
                if len(lucky_peasants_to_be_relocated) <= 0:
                    break
                buses_with_relocated_peasants[bus_num] = lucky_peasants_to_be_relocated[:space]
                lucky_peasants_to_be_relocated = lucky_peasants_to_be_relocated[space:]

            # Append to each line of assignmentscopy that which corresponds to buses_with_relocated_peasants
            new_output_attempt_i = open(output_category_path + "/attemptsfor{}/".format(input_name) + "{}".format(i), "w")
            # new_assignments = [assignments[i] + [] for i in range(len(assignments))] # deep copy of assignments
            # for i in range(len(new_assignments)):
            #     for peasant in lucky_peasants_to_be_relocated_copy:
            #         if peasant in new_assignments[i]:
            #             new_assignments[i].remove(peasant)

            for j in buses_with_relocated_peasants.keys():
                assignmentscopy[j] = assignmentscopy[j] + buses_with_relocated_peasants[j]
            for j in range(len(assignments)):
                new_output_attempt_i.write("{}\n".format(assignmentscopy[j]))
            new_output_attempt_i.close()

        random_scores = []
        if not os.path.isdir(output_category_path + "/attemptsfor{}".format(input_name)):
            os.mkdir(output_category_path + "/attemptsfor{}".format(input_name))
        for i in range(100): # want 100 random attempts
            random_replacement_attempt(i)
            score, msg = score_output(input_folder, output_category_path + "/attemptsfor{}".format(input_name) + "/{}".format(i))
            random_scores.append(score)
        keep_this = random_scores.index(max(random_scores))
        # Now replace the old outputfile with the new best of outputs
        output.close()
        # print("attempting copyfile")
        # print(output_category_path, "/attemptsfor{}".format(input_name), "{}".format(keep_this), output_file )
        copyfile(output_category_path + "/attemptsfor{}/".format(input_name) + "{}".format(keep_this), output_file)
        # print("successful copyfile call")

    def recursive_solve(ubfactor="6", nruns="1", ctype="1", rtype="1", otype="1", vcycle="2", dbglvl="0", reconst="1", num_attempts=0):
        # if num_attempts >= 9:
        #     return -1 # -1 rv means too many attempts
        numparts = str(num_buses)
        # ubfactor = "6"
        # nruns = "1"
        # ctype = "1"
        # # rtype or otype is hmetis vs khmetis specific
        # vcycle = "1"
        if num_buses <= 16:
            # want to use hmetis
            # rtype = "1"
            # reconst = "1"
            # dbglvl = "0"
            call(['./hmetis-1.5-linux/hmetis', hmetis_input_path, numparts, ubfactor, nruns, ctype, rtype, vcycle, reconst, dbglvl])
        else:
            # want to use khmetis
            # otype = "1"
            # dbglvl = "0"
            call(['./hmetis-1.5-linux/khmetis', hmetis_input_path, numparts, ubfactor, nruns, ctype, otype, vcycle, dbglvl])

        # try:
        parse_output()
        if check_bus_overfill():
            # if int(ubfactor) <= 10:
            #     ubfactor = str(int(ubfactor) - 1)
            # else:
            #     ubfactor = str(int(ubfactor) - 5)
            # a = recursive_solve(ubfactor=ubfactor, num_attempts=num_attempts+1) # try to tighten the even-ness constraint
            # if a < 0:
            manual_bus_stalin_relocation() # we can manually re-shape buses if tightening ubfactor fails
                # a = recursive_solve(ubfactor=ubfactor, ) # in this frame, ubfactor is still 1 and num_attempts is still 9
        # except FileNotFoundError: # this is the case where there exists an empty bus
        #     pass # we'll ignore this for now

    if num_buses < 2:  # this case is trivial, simply load everyone on the bus!
        hmetis_input_graph = open(hmetis_input_path)
        firstline = hmetis_input_graph.readline()
        second_num = int(firstline.split(" ")[1])
        hmetis_output_partitions = open(hmetis_output_path + "/hmetis_input.graph.part.1", "w")
        for i in range(second_num):
            hmetis_output_partitions.write("0\n")
        parse_output()

    recursive_solve()


    # # TODO: edit the try/except to recursively call solve and fiddle with parameters.  use a new parameter
    # #   num tries in order to have a base case.
    # try:
    #     open(hmetis_input_path + ".part." + str(num_buses))
    # except FileNotFoundError:
    #     rtype = "1"
    #     reconst = "1"
    #     dbglvl = "0"
    #     call(['./hmetis-1.5-linux/hmetis', hmetis_input_path, numparts, ubfactor, nruns, ctype, rtype, vcycle, reconst, dbglvl])
    # try:
    #     open(hmetis_input_path + ".part." + str(num_buses))
    # except FileNotFoundError:
    #     num_attempts += 1
    #     if num_attempts <= 10:
    #         recursive_solve(ubfactor="2", reconst="0", num_attempts=num_attempts)
    #     else:
    #         pass # give up




def main():
    '''
        Main method which iterates over all inputs and calls `solve` on each.
        The student should modify `solve` to return their solution and modify
        the portion which writes it to a file to make sure their output is
        formatted correctly.
    '''
    size_categories = ["medium", "large"] # removed medium and large
    tasks = []

    if not os.path.isdir(path_to_outputs):
        os.mkdir(path_to_outputs)

    for size in size_categories:
        category_path = path_to_inputs + "/" + size
        output_category_path = path_to_outputs + "/" + size
        category_dir = os.fsencode(category_path)

        if not os.path.isdir(output_category_path):
            os.mkdir(output_category_path)

        for input_folder in os.listdir(category_dir):
            input_name = os.fsdecode(input_folder)
            tasks.append((category_path, input_name, output_category_path))
    pool = Pool(3) # I have a 4 core machine and want 1 to be free for general use
    results = [pool.apply_async(each_input_task, t) for t in tasks]
    pool.close()
    pool.join()

    #
    # if not os.path.isdir(path_to_outputs):
    #     os.mkdir(path_to_outputs)
    #
    # for size in size_categories:
    #     category_path = path_to_inputs + "/" + size
    #     output_category_path = path_to_outputs + "/" + size
    #     category_dir = os.fsencode(category_path)
    #
    #     if not os.path.isdir(output_category_path):
    #         os.mkdir(output_category_path)
    #
    #     for input_folder in os.listdir(category_dir):
    #         print(input_folder)
    #         input_name = os.fsdecode(input_folder)
    #         hmetis_input_path, num_buses, size_bus, hmetis_output_path, nodelist = parse_input(category_path + "/" + input_name)
    #         solve(hmetis_input_path, num_buses, size_bus, hmetis_output_path)
    #
    #         output_file = open(output_category_path + "/" + input_name + ".out", "w")
    #         #
    #         # #TODO: modify this to write your solution to your
    #         # #      file properly as it might not be correct to
    #         # #      just write the variable solution to a file
    #         #
    #         # # need to use hmetis_output_path in order to read the hmetis output file, parse it, and
    #         # # produce a viable cs170 scorable output.  Remember to start counting from 0 for the outputs,
    #         # # because all the node labels were artificially incremented in the input parser, whereas they
    #         # # don't need to be and shouldn't be artificially incremented in the output parser.
    #         current_node = 0
    #         partitionmap = {i:[] for i in range(num_buses)}
    #         partitions = open(hmetis_input_path + ".part." + str(num_buses))
    #         for line in partitions:
    #             line = int(line)
    #             # this turns the partition number into an integer type
    #             partitionmap[line].append(nodelist[current_node])
    #             current_node += 1
    #         for partition in partitionmap.keys():
    #             output_file.write("{}\n".format(partitionmap[partition]))
    #
    #         # #####
    #         output_file.close()

def each_input_task(category_path, input_name, output_category_path):
    # print(input_name)
    hmetis_input_path, num_buses, size_bus, hmetis_output_path, nodelist = parse_input(
        category_path + "/" + input_name)
    solve(hmetis_input_path, num_buses, size_bus, hmetis_output_path, nodelist, category_path, input_name, output_category_path)
    # previously, parsing outputs was in each_input_task, but it has been moved to solve.  Now, each_input_task
    # only involves parsing inputs and calling solve



    # moved the below into solve
    # output_file = open(output_category_path + "/" + input_name + ".out", "w")
    # #
    # # #TODO: modify this to write your solution to your
    # # #      file properly as it might not be correct to
    # # #      just write the variable solution to a file
    # #
    # # # need to use hmetis_output_path in order to read the hmetis output file, parse it, and
    # # # produce a viable cs170 scorable output.  Remember to start counting from 0 for the outputs,
    # # # because all the node labels were artificially incremented in the input parser, whereas they
    # # # don't need to be and shouldn't be artificially incremented in the output parser.
    # current_node = 0
    # partitionmap = {i: [] for i in range(num_buses)}
    # partitions = open(hmetis_input_path + ".part." + str(num_buses))
    # for line in partitions:
    #     line = int(line)
    #     # this turns the partition number into an integer type
    #     partitionmap[line].append(nodelist[current_node])
    #     current_node += 1
    # for partition in partitionmap.keys():
    #     output_file.write("{}\n".format(partitionmap[partition]))
    #
    # # #####
    # output_file.close()


if __name__ == '__main__':
    main()


