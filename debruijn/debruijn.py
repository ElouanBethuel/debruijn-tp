#!/bin/env python3
# -*- coding: utf-8 -*-
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    A copy of the GNU General Public License is available at
#    http://www.gnu.org/licenses/gpl-3.0.html

"""Perform assembly based on debruijn graph."""

import argparse
import os
import sys
import networkx as nx
import matplotlib
from operator import itemgetter
import random
random.seed(9001)
from random import randint
import statistics
import textwrap
import matplotlib.pyplot as plt
matplotlib.use("Agg")

__author__ = "Your Name"
__copyright__ = "Universite Paris Diderot"
__credits__ = ["Your Name"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Your Name"
__email__ = "your@email.fr"
__status__ = "Developpement"

def isfile(path): # pragma: no cover
    """Check if path is an existing file.

    :param path: (str) Path to the file
    
    :raises ArgumentTypeError: If file doesn't exist
    
    :return: (str) Path 
    """
    if not os.path.isfile(path):
        if os.path.isdir(path):
            msg = "{0} is a directory".format(path)
        else:
            msg = "{0} does not exist.".format(path)
        raise argparse.ArgumentTypeError(msg)
    return path


def get_arguments(): # pragma: no cover
    """Retrieves the arguments of the program.

    :return: An object that contains the arguments
    """
    # Parsing arguments
    parser = argparse.ArgumentParser(description=__doc__, usage=
                                     "{0} -h"
                                     .format(sys.argv[0]))
    parser.add_argument('-i', dest='fastq_file', type=isfile,
                        required=True, help="Fastq file")
    parser.add_argument('-k', dest='kmer_size', type=int,
                        default=22, help="k-mer size (default 22)")
    parser.add_argument('-o', dest='output_file', type=str,
                        default=os.curdir + os.sep + "contigs.fasta",
                        help="Output contigs in fasta file (default contigs.fasta)")
    parser.add_argument('-f', dest='graphimg_file', type=str,
                        help="Save graph as an image (png)")
    return parser.parse_args()


def read_fastq(fastq_file):
    """Extract reads from fastq files.

    :param fastq_file: (str) Path to the fastq file.
    :return: A generator object that iterate the read sequences. 
    """
    with open(fastq_file, 'r') as filin:
        for line in filin:
            yield next(filin).strip()
            next(filin)
            next(filin)
    pass


def cut_kmer(read, kmer_size):
    """Cut read into kmers of size kmer_size.
    
    :param read: (str) Sequence of a read.
    :return: A generator object that iterate the kmers of of size kmer_size.
    """
    for i in range(len(read) - kmer_size + 1):
        kmer = read[i:i + kmer_size]
        yield kmer   
    pass

def build_kmer_dict(fastq_file, kmer_size):
    """Build a dictionnary object of all kmer occurrences in the fastq file

    :param fastq_file: (str) Path to the fastq file.
    :return: A dictionnary object that identify all kmer occurrences.
    """
    kmer_dict = {}
    for read in read_fastq(fastq_file):
        for kmer in cut_kmer(read, 3):
            if kmer in kmer_dict:
                kmer_dict[kmer] += 1
            else:
                kmer_dict[kmer] = 1
    return kmer_dict
    pass

def build_graph(kmer_dict):
    """Build the debruijn graph

    :param kmer_dict: A dictionnary object that identify all kmer occurrences.
    :return: A directed graph (nx) of all kmer substring and weight (occurrence).
    """
    graph = nx.DiGraph()

    for kmer, count in kmer_dict.items():
    
        prefix = kmer[:-1]
        suffix = kmer[1:]

        if not graph.has_node(prefix):
            graph.add_node(prefix)
        if not graph.has_node(suffix):
            graph.add_node(suffix)

        if graph.has_edge(prefix, suffix):
            graph[prefix][suffix]['weight'] += count
        else:
            graph.add_edge(prefix, suffix, weight=count)
            
    return graph
    
    pass


def remove_paths(graph, path_list, delete_entry_node, delete_sink_node):
    """Remove a list of path in a graph. A path is set of connected node in
    the graph

    :param graph: (nx.DiGraph) A directed graph object
    :param path_list: (list) A list of path
    :param delete_entry_node: (boolean) True->We remove the first node of a path 
    :param delete_sink_node: (boolean) True->We remove the last node of a path
    :return: (nx.DiGraph) A directed graph object
    """
    new_graph = graph.copy()
    
    for path in path_list:
    
        if delete_entry_node == True and delete_sink_node == True:
            new_graph.remove_nodes_from(path)
            
        elif delete_entry_node == True and delete_sink_node == False:
            new_graph.remove_nodes_from(path[:-1])
            
        elif delete_entry_node == False and delete_sink_node == True:
            new_graph.remove_nodes_from(path[1:])
        
        else:
            new_graph.remove_nodes_from(path[1:-1])
                    
    return new_graph 
    pass


def select_best_path(graph, path_list, path_length, weight_avg_list, 
                     delete_entry_node=False, delete_sink_node=False):
    """Select the best path between different paths

    :param graph: (nx.DiGraph) A directed graph object
    :param path_list: (list) A list of path
    :param path_length: (list) A list of length of each path
    :param weight_avg_list: (list) A list of average weight of each path
    :param delete_entry_node: (boolean) True->We remove the first node of a path 
    :param delete_sink_node: (boolean) True->We remove the last node of a path
    :return: (nx.DiGraph) A directed graph object
    """
    
    std_poids = statistics.stdev(weight_avg_list) # calcul écart-type sur les poids 
    std_long = statistics.stdev(path_length) # calcul écart-type sur les longueurs 
    
    if std_poids > 0:
        best_path_index = weight_avg_list.index(max(weight_avg_list))  
        
    else:
        if std_long > 0:
            best_path_index = path_length.index(max(path_length))
        else:
           best_path_index = random.randint(0, len(path_list)-1)
        
    best_path = path_list[best_path_index]
    
    for path in path_list:
        if path != best_path:
            graph = remove_paths(graph, [path], delete_entry_node, delete_sink_node)
    
    return graph
    pass

def path_average_weight(graph, path):
    """Compute the weight of a path

    :param graph: (nx.DiGraph) A directed graph object
    :param path: (list) A path consist of a list of nodes
    :return: (float) The average weight of a path
    """
    return statistics.mean([d["weight"] for (u, v, d) in graph.subgraph(path).edges(data=True)])

def solve_bubble(graph, ancestor_node, descendant_node):
    """Explore and solve bubble issue

    :param graph: (nx.DiGraph) A directed graph object
    :param ancestor_node: (str) An upstream node in the graph 
    :param descendant_node: (str) A downstream node in the graph
    :return: (nx.DiGraph) A directed graph object
    """
    
    paths = list(nx.all_simple_paths(graph, ancestor_node, descendant_node))
    path_long = []
    path_poid = []
    
    for path in paths:
        path_long.append(len(path))
        path_poid.append(path_average_weight(graph, path))

    graph = select_best_path(graph, paths, path_long, path_poid, delete_entry_node=False, delete_sink_node=False)
    
    return graph
    pass

def simplify_bubbles(graph):
    """Detect and explode bubbles

    :param graph: (nx.DiGraph) A directed graph object
    :return: (nx.DiGraph) A directed graph object
    """
    
    bubble = False 
    list_nodes_graph = list(graph.nodes())
    
    for node in list_nodes_graph:
        list_predecessors =  list(graph.predecessors(node))
        
        if len(list_predecessors) > 1:
        
            combinations = [(list_predecessors[i], list_predecessors[j]) for i in range(0, len(list_predecessors)-1) for j in range(i+1, len(list_predecessors)) if i != j]
            
            for combination in combinations:
            
                noeud_ancetre = nx.lowest_common_ancestor(graph, combination[0], combination[1])
                
                if noeud_ancetre is not None:
                    bubble = True
                    break
             
        if bubble:
            break
                    
    if bubble:
        graph = simplify_bubbles(solve_bubble(graph, noeud_ancetre, node))
        
    return graph
  

def solve_entry_tips(graph, starting_nodes):
    """Remove entry tips

    :param graph: (nx.DiGraph) A directed graph object
    :return: (nx.DiGraph) A directed graph object
    """
    
    path_list = [list(nx.all_simple_paths(graph, start, node)) for node in graph.nodes for start in starting_nodes if len(list(graph.predecessors(node))) > 1]
    
    if path_list:
        path_length = [len(path) for paths in path_list for path in paths]
        weight_avg = [path_average_weight(graph, path) for paths in path_list for path in paths]
        graph = select_best_path(graph, [path for paths in path_list for path in paths], path_length, weight_avg, delete_entry_node=True, delete_sink_node=False)
    
    return graph



def solve_out_tips(graph, ending_nodes):
    """Remove out tips

    :param graph: (nx.DiGraph) A directed graph object
    :return: (nx.DiGraph) A directed graph object
    """
    path_list = [list(nx.all_simple_paths(graph, node, end)) for node in graph.nodes for end in ending_nodes if len(list(graph.successors(node))) > 1]
    
    if path_list:
        path_length = [len(path) for paths in path_list for path in paths]
        weight_avg = [path_average_weight(graph, path) for paths in path_list for path in paths]
        graph = select_best_path(graph, [path for paths in path_list for path in paths], path_length, weight_avg, delete_entry_node=False, delete_sink_node=True)
    
    return graph

def get_starting_nodes(graph):
    """Get nodes without predecessors

    :param graph: (nx.DiGraph) A directed graph object
    :return: (list) A list of all nodes without predecessors
    """
    list_start_nodes = []
    for node in graph.nodes():
        if len(list(graph.predecessors(node))) == 0: #obligé de convertir en list car itérateur, si la list est vide noeud sans predecesseur
            list_start_nodes.append(node)
    return list_start_nodes
    pass

def get_sink_nodes(graph):
    """Get nodes without successors

    :param graph: (nx.DiGraph) A directed graph object
    :return: (list) A list of all nodes without successors
    """
    list_sink_nodes = []
    for node in graph.nodes():
        if len(list(graph.successors(node))) == 0: #obligé de convertir en list car itérateur, si la list est vide noeud sans sucesseur
            list_sink_nodes.append(node)
    return list_sink_nodes
    pass

def get_contigs(graph, starting_nodes, ending_nodes):
    """Extract the contigs from the graph

    :param graph: (nx.DiGraph) A directed graph object 
    :param starting_nodes: (list) A list of nodes without predecessors
    :param ending_nodes: (list) A list of nodes without successors
    :return: (list) List of [contiguous sequence and their length]
    """
    list_tuple_contigs = []
    
    for node_start in starting_nodes:
        for node_target in ending_nodes:
        
            if nx.has_path(graph, node_start, node_target) == True:      # regard s'il existe un chemin entre noeud de départ et noeud de fin 
                all_contigs = nx.all_simple_paths(graph, node_start, node_target) # récupère tt les chemin entre c'est deux noeuds
                
                for contig in all_contigs:
                    contig_sequence = ""
                    
                    for node in contig:
                        if len(contig_sequence) == 0:
                            contig_sequence += node
                        else:
                            contig_sequence += node[-1]
                   
                    list_tuple_contigs.append((contig_sequence,len(contig_sequence)))
                        
    return list_tuple_contigs        
    pass

def save_contigs(contigs_list, output_file):
    """Write all contigs in fasta format

    :param contig_list: (list) List of [contiguous sequence and their length]
    :param output_file: (str) Path to the output file
    """
    
    with open(output_file, 'w') as file:
    
        for index, (contig, length) in enumerate(contigs_list):
            header = f">contig_{index} len={length}\n"
            file.write(header)
            wrapped_contig = textwrap.fill(contig, width=80)
            file.write(wrapped_contig + '\n')
    pass


def draw_graph(graph, graphimg_file): # pragma: no cover
    """Draw the graph

    :param graph: (nx.DiGraph) A directed graph object
    :param graphimg_file: (str) Path to the output file
    """                                   
    fig, ax = plt.subplots()
    elarge = [(u, v) for (u, v, d) in graph.edges(data=True) if d['weight'] > 3]
    #print(elarge)
    esmall = [(u, v) for (u, v, d) in graph.edges(data=True) if d['weight'] <= 3]
    #print(elarge)
    # Draw the graph with networkx
    #pos=nx.spring_layout(graph)
    pos = nx.random_layout(graph)
    nx.draw_networkx_nodes(graph, pos, node_size=6)
    nx.draw_networkx_edges(graph, pos, edgelist=elarge, width=6)
    nx.draw_networkx_edges(graph, pos, edgelist=esmall, width=6, alpha=0.5, 
                           edge_color='b', style='dashed')
    #nx.draw_networkx(graph, pos, node_size=10, with_labels=False)
    # save image
    plt.savefig(graphimg_file)


#==============================================================
# Main program
#==============================================================
def main(): # pragma: no cover
    """
    Main program function
    """
    # Get arguments
    args = get_arguments()
    kmer_dict = build_kmer_dict(args.fastq_file, 200)
    graph = build_graph(kmer_dict)
    
    list_start_nodes = get_starting_nodes(graph)
    list_sink_nodes = get_sink_nodes(graph)
    
    list_tuple_contigs = get_contigs(graph, list_start_nodes, list_sink_nodes)
    save_contigs(list_tuple_contigs, args.output_file)
    
    # Fonctions de dessin du graphe
    # A decommenter si vous souhaitez visualiser un petit 
    # graphe
    # Plot the graph
    if args.graphimg_file:
        draw_graph(graph, args.graphimg_file)


if __name__ == '__main__': # pragma: no cover
    main()







    
