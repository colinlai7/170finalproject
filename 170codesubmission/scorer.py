import os
import networkx as nx
import numpy as np
from subprocess import call



def score_output(input_folder, output_file):
    '''
        Takes an input and an output and returns the score of the output on that input if valid

        Inputs:
            input_folder - a string representing the path to the input folder
            output_file - a string representing the path to the output file

        Outputs:
            (score, msg)
            score - a number between 0 and 1 which represents what fraction of friendships were broken
            msg - a string which stores error messages in case the output file is not valid for the given input
    '''
    graph = nx.read_gml(input_folder + "/graph.gml")
    parameters = open(input_folder + "/parameters.txt")
    num_buses = int(parameters.readline())
    size_bus = int(parameters.readline())
    constraints = []

    for line in parameters:
        line = line[1: -2]
        curr_constraint = [node.replace("'", "") for node in line.split(", ")]
        constraints.append(curr_constraint)

    output = open(output_file)
    assignments = []
    for line in output:
        line = line[1: -2]
        curr_assignment = [node.replace("'", "") for node in line.split(", ")]
        assignments.append(curr_assignment)

    if len(assignments) != num_buses:
        return -1, "Must assign students to exactly {} buses, found {} buses".format(num_buses, len(assignments))

    # make sure no bus is empty or above capacity
    for i in range(len(assignments)):
        if len(assignments[i]) > size_bus:
            return -1, "Bus {} is above capacity".format(i)
        if len(assignments[i]) <= 0:
            return -1, "Bus {} is empty".format(i)

    bus_assignments = {}
    attendance_count = 0

    # make sure each student is in exactly one bus
    attendance = {student: False for student in graph.nodes()}
    for i in range(len(assignments)):
        if not all([student in graph for student in assignments[i]]):
            return -1, "Bus {} references a non-existant student: {}".format(i, assignments[i])

        for student in assignments[i]:
            # if a student appears more than once
            if attendance[student] == True:
                print(assignments[i])
                return -1, "{0} appears more than once in the bus assignments".format(student)

            attendance[student] = True
            bus_assignments[student] = i

    # make sure each student is accounted for
    if not all(attendance.values()):
        return -1, "Not all students have been assigned a bus"

    total_edges = graph.number_of_edges()
    # Remove nodes for rowdy groups which were not broken up
    for i in range(len(constraints)):
        busses = set()
        for student in constraints[i]:
            busses.add(bus_assignments[student])
        if len(busses) <= 1:
            for student in constraints[i]:
                if student in graph:
                    graph.remove_node(student)

    # score output
    score = 0
    for edge in graph.edges():
        if bus_assignments[edge[0]] == bus_assignments[edge[1]]:
            score += 1
    score = score / total_edges

    return score, "Valid output submitted with score: {}".format(score)

# path_to_inputs = "./skeleton/all_inputs"
# path_to_outputs = "./skeleton/outputs"
#
# size_categories = ["small"]
# scores = []
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
#         input_name = os.fsdecode(input_folder)
#         print(input_name)
#         score, _ = score_output(category_path + "/" + input_name, output_category_path + "/" + input_name + ".out")
#         if score < 0:
#             print("asdf problem")
#         scores.append(score)
#
#         # call(["python3", "./skeleton/output_scorer.py", category_path + "/" + input_name, output_category_path + "/" + input_name + ".out"])
#
# print(np.mean(scores))
