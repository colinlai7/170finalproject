import networkx as nx
import os
import output_scorer
from shutil import copy
from pathlib import Path



###########################################
# Change this variable to the path to
# the folder containing all three input
# size category folders
###########################################
path_to_inputs = "./inputs"

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
    parameters = open(folder_name + "/parameters.txt")
    num_buses = int(parameters.readline())
    size_bus = int(parameters.readline())
    constraints = []

    for line in parameters:
        line = line[1: -2]
        curr_constraint = [num.replace("'", "") for num in line.split(", ")]
        constraints.append(curr_constraint)

    return graph, num_buses, size_bus, constraints

def solve():
    #TODO: Write this method as you like. We'd recommend changing the arguments here as well
    pass

def main():
    '''
        Main method which iterates over all inputs and calls `solve` on each.
        The student should modify `solve` to return their solution and modify
        the portion which writes it to a file to make sure their output is
        formatted correctly.
    '''
    size_categories = ["small", "medium", "large"]
    if not os.path.isdir(path_to_outputs):
        os.mkdir(path_to_outputs)

    for size in size_categories:
        category_path = path_to_inputs + "/" + size
        output_category_path = path_to_outputs + "/" + size

        category_path1 = "./outputs1/" + size
        category_path2 = "./outputs2/" + size
        category_dir = os.fsencode(category_path)

        if not os.path.isdir(output_category_path):
            os.mkdir(output_category_path)

        for input_folder in os.listdir(category_dir):
            input_name = os.fsdecode(input_folder)
            graph, num_buses, size_bus, constraints = parse_input(category_path + "/" + input_name)

            inpath = category_path + "/" + input_name
            outpath1 = category_path1 + "/" + input_name + ".out"
            outpath2 = category_path2 + "/" + input_name + ".out"

            outputpath = output_category_path + "/" + input_name + ".out"



            if Path(outpath1).is_file() and Path(outpath2).is_file():
                # run output_scorer on each output
                score1, msg = output_scorer.score_output(inpath, outpath1)
                score2, msg = output_scorer.score_output(inpath, outpath2)
                print("Got Score1: ")
                print(score1)
                print("Got Score2: ")
                print(score2)
                if score1 == None and score2 == None:
                    print("no score for both")
                elif score1 > score2:
                    print("COPYING OUTPUT1, HIGHER SCORE")
                    copy(outpath1, outputpath)
                elif score2 > score1:
                    print("COPYING OUTPUT2, HIGHER SCORE")
                    copy(outpath2, outputpath)
                elif score1 == score2:
                    if (score1 == -1) and (score2 == -1):
                        print("both invalid")
                    print("TIE: COPYING OUTPUT1")
                    copy(outpath1, outputpath)
                else:
                    print("Else Error")

            elif (not Path(outpath1).is_file()) and (not Path(outpath2).is_file()):
                print("no file for either path:")
                print(input_name)
                continue
            elif not Path(outpath1).is_file():
                print("COPYING OUTPUT2, no output1 file")
                copy(outpath2, outputpath)
            elif not Path(outpath2).is_file():
                print("COPYING OUTPUT1, no output2 file")
                copy(outpath1, outputpath)
            # print(output_category_path)
            # print(outpath1)
            # break
            # solution = solve(graph, num_buses, size_bus, constraints)
            # output_file = open(output_category_path + "/" + input_name + ".out", "w")
            #
            # #TODO: modify this to write your solution to your
            # #      file properly as it might not be correct to
            # #      just write the variable solution to a file
            # output_file.write(solution)

            # output_file.close()

if __name__ == '__main__':
    main()
