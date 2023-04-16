#!/usr/bin/python3
import sys
import pickle
import argparse

from typing import *

def run_search(dict_file: str, postings_file: str, queries_file: str, 
               results_file: str, thesaurus_file: str):
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
    arg_parser.add_argument('-d', dest='dictionary_file', required=True)
    arg_parser.add_argument('-p', dest='postings_file', required=True)
    arg_parser.add_argument('-q', dest='queries_file', required=True)
    arg_parser.add_argument('-o', dest='output_file', required=True)
    arg_parser.add_argument('-t', dest='thesaurus_file')
    args = arg_parser.parse_args()

    run_search(args.dictionary_file, args.postings_file, args.queries_file,
               args.output_file, args.thesaurus_file)