import networkx as nx
import os
import random
import queue as Q
import sys

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
path_to_outputs = "./outputs1"

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

# use global to modify in other functions
diffqueues = [] #[Q.PriorityQueue() for _ in range(num_buses)]

def solve(graph, num_buses, size_bus, constraints):
    #TODO: Write this method as you like. We'd recommend changing the arguments here as well

    # TESTINGSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS
    # testq = Q.PriorityQueue()
    # testq.put([0,"a", 5])
    # testq.put([-3, "b", 6])
    # print(testq.get()[0])
    # print(testq.queue)
    # val1, val2 = testq.get()[1:]
    # print(val1)
    # print(val2)
    # print(testq.get()[1:])
    # testq.put((-5, "c"))
    # print(testq.qsize())
    # print(testq.queue[0])
    # print(testq.queue[0][0])
    # print(testq.queue[0][1])
    # l = [1, 3]
    # m = l.copy()
    # print(m)
    # lst = [sys.maxsize, sys.maxsize]
    # print(lst[0])
    # print(sys.maxsize * sys.maxsize)
    # return

    # initialize data structures
    # buses, subsets of vertices
    capacities = [0 for _ in range(num_buses)]
    buses = [set() for _ in range(num_buses)]
    # priority queues of diffs for each bus, subset
    # diffqueues = [Q.PriorityQueue() for _ in range(num_buses)]

    # if more busses than students no solution
    if num_buses > len(graph):
        print("no solution")
        return None

    remaining = graph.copy()
    print(list(remaining.nodes))

    # before adding seed, account for single rowdy groups
    # fill buses with single rowdy groups and set capacity to full until filling with rest
    # seedindex = 0
    singles = list(getsinglerowdy(constraints))

    # used as starting index for non-rowdy buses (seed)
    r = 0
    # print(singles)

    if len(singles) > 0:
        # iterate through each single rowdy group
        for v in singles:
            # if bus is not full: add to bus, remove from graph, and increment capacity
            # if bus is full, increment r index
            if not capacities[r] < size_bus:
                r += 1
            # check if no buses left:
            if r >= num_buses:
                print("r >= num_buses")
                return buses
            # print(type(v[0]))
            buses[r].add(str(v))
            capacities[r] +=1
            remaining.remove_node(str(v))

        # starting seed is the next bus after single rowdy buses
        r += 1
    # otherwise starting seed remains 0
    else:
        r = 0
    # if no more bues to fill, then return
    if r >= num_buses:
        print("r >= num_buses second check")
        return buses

    # risk of putting same optimal separately
    # seed buses with random nodes of max neighbors
    # LATER TAKE CONSTRAINTS INTO ACCOUNT
    # seedbuses()

    # generate random first vertex and add to set
    seed = random.sample(remaining.nodes, 1)
    # print(type(seed)) # list
    # print(type(seed[0])) # string
    print(seed[0])
    buses[r].add(str(seed[0]))
    capacities[r] += 1
    # remove seed from remaining
    remaining.remove_node(str(seed[0]))
    # print(list(remaining.nodes))

    # initialize diffqueues
    global diffqueues
    diffqueues = [Q.PriorityQueue() for _ in range(num_buses)]
    for j in range(num_buses):
        # don't update if bus at capacity
        if capacities[j] == size_bus:
            continue
        # update diff for all remaining nodes
        for v in remaining.nodes:
            difference = diff(v, j, buses, graph)
            diffqueues[j].put(difference)
    print("diffqueue initialized")


    # remaining.remove_node(str(5))
    # print(list(remaining.nodes))
    # test here
    # neighbors = list(graph.neighbors(seed[0]))
    # for n in neighbors:
    #     print(type(n))
    #     print(n)
    # return
    # main loop
    while len(remaining.nodes) > 0:
        # print(len(remaining.nodes))
        # calculate minval for each set
        minvalq = Q.PriorityQueue()
        # diffqueues = [Q.PriorityQueue() for _ in range(num_buses)]
        # keep track of minval for each set
        minval = [sys.maxsize for _ in range(num_buses)]
        # loop through each bus/subset
        print("in loop")
        # for j in range(num_buses):
        #     # don't update if bus at capacity
        #     if capacities[j] == size_bus:
        #         continue
        #     # update diff for all remaining nodes
        #     for v in remaining.nodes:
        #         difference = diff(v, j, buses, graph)
        #         diffqueues[j].put(difference)
        #     # update minval if there is a new minval

        for j in range(num_buses):
            # CHANGEPOP
            # print(j)
            if diffqueues[j].qsize() > 0:
                qpop = diffqueues[j].get()
                diffqueues[j].put(qpop)
                # if qpop[0] < minval:
                minval[j] = qpop[0]
            # end change
            # if diffqueues[j].queue[0][0] < minval:
            #     minval = diffqueues[j].queue[0][0]

        # if all minval is max, then remaining vertices have no neighbors, fill
        # sum of minvals of valid buses, over length of minvals of valid buses
        # optimization technique to prevent extra computations
        if (len(minval[r:]) > 0) and (sum(minval[r:])/len(minval[r:]) == sys.maxsize):
            # CHANGE THIS TO TAKE CONSTRAINTS INTO ACCOUNT LATER
            print("all minval is maxsize now")
            for j in range(num_buses):
                # don't update if bus at capacity
                # if capacities[j] == size_bus:
                #     continue
                while capacities[j] < size_bus:
                    # if no more remaining nodes, return
                    if len(remaining.nodes) == 0:
                        return buses
                    node = random.sample(remaining.nodes, 1)[0]
                    print(type(node))
                    buses[j].add(node)
                    remaining.remove_node(node)
                    capacities[j] += 1
            return buses

        # determine addset: subset to add to, less than average subset size not including rowdy buses
        nonrowdycap = capacities[r:]
        avgsubsetsize = sum(nonrowdycap)/len(nonrowdycap)
        possubsets = set()
        currmin = sys.maxsize
        for i in range(num_buses):
            # if it's below the average subset size, and it's the minimum of all those, then select it
            # as the next subset to add, and populate mivalq
            if capacities[i] <= avgsubsetsize:
                # if less, then restart list
                if minval[i] < currmin:
                    possubsets = set()
                    possubsets.add(i)
                    currmin = minval[i]
                # if equal, then add to list
                if minval[i] == currmin:
                    possubsets.add(i)
        # choose a subset
        # RANDOM, CHANGE LATER
        # print(avgsubsetsize)
        setidx = random.sample(possubsets, 1)[0]
        # print(setidx)
        # loop through diffqueue of setidx to add to minvalq
        buffer = []
        while not diffqueues[setidx].empty():
            curr = diffqueues[setidx].get()
            buffer.append(curr)
            if curr[0] == minval[setidx]:
                element = [-curr[2], curr[1], setidx]
                minvalq.put(element)
            # once current diff val is not minval[addset], then exit the loop
            else:
                break
        # readd popped diffs back into diffqueue
        for b in buffer:
            diffqueues[setidx].put(b)
        print(minval)
        print("minvalq size")
        print(minvalq.qsize())


        # # loop through diffqueues to add to minvalq
        # for j in range(num_buses):
        #     # don't update if bus at capacity
        #     if capacities[j] == size_bus:
        #         continue
        #     # add minimum(s) of each set in minvalq
        #     for v in range(diffqueues[j].qsize()):
        #         # CHANGEPOP
        #         # probably don't need to change
        #         if diffqueues[j].queue[v][0] == minval:
        #             # append the set it appears in, then add to minvalq
        #             # order by neighbors, negative for priority
        #             difference = diffqueues[j].queue[v].copy()
        #             # [-neighbors, v, j]
        #             element = [-difference[2], difference[1], j]
        #             minvalq.put(element)
        #         # delete break because queue is not sorted, only heap sorted!
        #         # else:
        #         #     break


        # now pick a vertex if theres more than 1 in minvalq breaking ties based on a heuristic
        # break ties based on max neighbors, otherwise some other heuristic (to add)
        vadd = None
        jadd = None
        vadd, jadd = breakties(minvalq)


        # add vertex to bus and update capacity
        buses[jadd].add(str(vadd))
        capacities[jadd] += 1
        # remove node from graph
        print("vadd")
        print(vadd)
        print(jadd)
        # remaining.remove_node(str(vadd))

        # update diff and delete diff
        # update diff of neighbors
        update(str(vadd), jadd, remaining)
        remaining.remove_node(str(vadd))

        # delete diff
        print("remaining after")
        print(list(remaining.nodes))
        # add minval to a Set

    return buses
    # print(len(remaining.nodes))
    # print(remaining.degree[seed[0]])

    # print(buses[0])
    # diff(seed, buses[0], graph)

def getsinglerowdy(constraints):
    # returns all single rowdy groups to fill buses
    singles = set()
    for group in constraints:
        # print("Single rowdy:")
        # print(len(group))
        # print(group)
        if len(group) == 1:
            if group[0] not in singles:
                singles.add(str(group[0]))
        # print(group)
    return singles

def breakties(minvalq):
    # break ties
    # if only one element, return it
    if minvalq.qsize() == 1:
        return minvalq.get()[1:]
    else:
        # print(minvalq.qsize())
        # maximize neightbors (minimize negative internal)
        bestset = set()
        # CHANGEPOP
        bestval = minvalq.queue[0][0]
        while not minvalq.empty():
            curr = minvalq.get()
            # if current element's neighbors are not the bestval, stop adding
            if curr[0] == bestval:
                bestset.add((curr[1], curr[2]))
            else:
                break
        # currv = minvalq.get()
        # bestval = currv[0]
        # while currv[0] == bestval:
        #     bestset.add(currv[1:])
        #     currv = minvalq.get()

        # return random choice from best set (for now?)
        return bestset.pop()


def initialize(graph):
    # initialize diff values
    # add least neighbors to each bus
    seedqueue = Q.PriorityQueue()

    for v in graph:
        # print(v)
        neighbors = len(graph.neighbors(v))
        print(neighbors)

    return


def update(v, subset, graph):
    # update diff values

    # if neighbor is for other set, external +=1, diff +=1
    global diffqueues
    neighbors = set(graph.neighbors(v))
    print(neighbors)
    # print(neighbors)
    # neighborset = set(neighbors)
    for j in range(len(diffqueues)):
        nset = neighbors.copy()
        vdeleted = False
        # for element in diffqueues[j]:
        # for idx in range(diffqueues[j].qsize()):
        buffer = []
        while diffqueues[j].qsize() > 0:
            # remove v and set vdeleted in this diffqueue to true
            # element = diffqueues[j].queue[idx]
            element = diffqueues[j].get()
            if element[1] == v:
                vdeleted = True
            # if vertex name is in set of neighbors
            elif element[1] in nset:
                nset.remove(element[1])
                # if neighbor is for j set, internal +=1 , diff -=1
                if subset == j:
                    element[0] -= 1
                # if neighbor is for other set, external +=1, diff +=1
                else:
                    element[0] += 1
                buffer.append(element)
            else: buffer.append(element)

            # stop once no neighbors left to account for and v not in buffer to add back
            if (len(nset) == 0) and (vdeleted):
                break
        # readd popped diffs back into diffqueue
        for b in buffer:
            diffqueues[j].put(b)

def delete():
    # delete a vertex from diff
    pass

def minsubset():
    # select next subset as the minimum subset
    # break ties based on constraints instead of randomly
    pass

def mindiff(pqueue):
    # find the remaining vertex with the minimum diff for a given subset
    # break ties based on constraints instead of randomly
    return
    return pqueue[0]

def diff(v, subset, buses, graph):
    # finds diff for a vertex and a subset
    # diff increase in cut size - new internal edges
    # v's edges across another set - v's edges in set
    neighbors = list(graph.neighbors(v))
    diff = 0
    internal = 0
    external = 0
    if len(neighbors) > 0:
        # loop through neighbors to add to external or internal
        for n in neighbors:
            for j in range(len(buses)):
                if n in buses[j]:
                    if subset == j:
                        internal += 1
                    else:
                        external += 1
        # external - internal
        diff = external - internal
        # diff = len(neighbors) - (2 * internal)
    else:
        print("no neighbors: ")
        print(v)
        diff =  sys.maxsize
    return [diff, v, len(neighbors)]


def main():
    '''
        Main method which iterates over all inputs and calls `solve` on each.
        The student should modify `solve` to return their solution and modify
        the portion which writes it to a file to make sure their output is
        formatted correctly.
    '''
    size_categories = ["large"] #["small", "medium", "large"]
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
            graph, num_buses, size_bus, constraints = parse_input(category_path + "/" + input_name)
            # print folder
            print("INPUT FOLDER:")
            print(str(input_folder))
            solution = solve(graph, num_buses, size_bus, constraints)
            # print solution
            if solution:
                for set in solution:
                    print(list(set))
            output_file = open(output_category_path + "/" + input_name + ".out", "w")
            print(output_category_path)
            print(input_name)
            #TODO: modify this to write your solution to your
            #      file properly as it might not be correct to
            #      just write the variable solution to a file
            # output_file.write(solution)
            if solution:
                for set in solution:
                    output_file.write(str(list(set)))
                    output_file.write("\n")
            output_file.close()

if __name__ == '__main__':
    main()
