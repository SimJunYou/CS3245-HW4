#!/usr/bin/python3
import sys
import pickle
import argparse

from typing import *

def usage():
    print(
        "usage: "
        + sys.argv[0]
        + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results -t thesaurus-pickle-file"
    )

def run_search(dict_file: str, postings_file: str, queries_file: str, results_file: str, thesaurus_file: str):
    """
    using the given dictionary file, postings file, and optionally thesaurus pickle file,
    perform searching on the given queries file and output the results to a file
    """
    print("running search on the queries...")

    query_tokens = []        
    if thesaurus_file:
        with open(thesaurus_file, "rb") as f:
            thesaurus = pickle.load(f)
        query_tokens = expand_query(["plaintiff"], thesaurus)
    print(query_tokens)

def expand_query(tokens: List[str], thesaurus: Dict[str, List[str]] = {}):
    """
    Expands a query token to include related terms.
    """
    result = []
    for token in tokens:
        result.append(token)
        result += thesaurus.get(token, [])
    return result

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-d', dest='dictionary_file', 
                            help='Path to the dictionary', required=True)
    arg_parser.add_argument('-p', dest='postings_file', 
                            help='Path to postings file', required=True)
    arg_parser.add_argument('-q', dest='file_of_queries', 
                            help='Path to queries file', required=True)
    arg_parser.add_argument('-o', dest='file_of_output', 
                            help='Path to output file', required=True)
    arg_parser.add_argument('-t', dest='thesaurus_file', 
                            help='(Optional) Path to thesaurus pickle file')
    args = arg_parser.parse_args()

    run_search(args.dictionary_file, args.postings_file, args.file_of_queries,
               args.file_of_output, args.thesaurus_file)