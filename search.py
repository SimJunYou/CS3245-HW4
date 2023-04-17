#!/usr/bin/python3
import pickle
import argparse
import json

from typing import Dict, List, Tuple
from Tokenizer import clean_query_token, tokenize_query
from QueryRefinement import expand_query, run_rocchio

def run_search(dict_file: str, postings_file: str, queries_file: str, results_file: str):
    """
    using the given dictionary file, postings file, and optionally 
    thesaurus pickle file, perform searching on the given queries 
    file and output the results to the results file
    """
    print("running search on the queries...")

    # Read config
    with open("config.json", "r") as cf:
        config = json.load(cf)
        RUN_QUERY_EXPANSION = config["run_query_expansion"]
        THESAURUS_FILENAME = config["file_names"]["thesaurus"]
        
        RUN_ROCCHIO = config["run_rocchio"]
        ALPHA = config["rocchio"]["alpha"]
        BETA = config["rocchio"]["beta"]

    # Read query file
    query_tokens = []
    relevant_docs = []
    with open(queries_file, "r") as qf:
        query = qf.readline()
        query_tokens = tokenize_query(query)
        while relevant_doc := qf.readline().strip():
            relevant_docs.append(relevant_doc)

    # if we are doing query expansion, we expand the query using
    # our thesaurus prebuilt from a legal text corpus
    print("Before", query_tokens)
    if RUN_QUERY_EXPANSION:
        with open(THESAURUS_FILENAME, "rb") as tf:
            thesaurus = pickle.load(tf)
        query_tokens = expand_query(query_tokens, thesaurus)
    print("After", query_tokens)

    # if RUN_ROCCHIO:
    #     run_rocchio(ALPHA, BETA)

    # # TODO: Write out result
    # result = ""
    # with open(results_file, "w") as rf:
    #     rf.write(result)

# python3 search.py -d dictionary.txt -p postings.txt -q queries/q1.txt -o results.txt
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-d', dest='dictionary_file', required=True)
    arg_parser.add_argument('-p', dest='postings_file', required=True)
    arg_parser.add_argument('-q', dest='queries_file', required=True)
    arg_parser.add_argument('-o', dest='output_file', required=True)
    args = arg_parser.parse_args()

    run_search(args.dictionary_file, args.postings_file, args.queries_file, args.output_file)
