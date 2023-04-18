#!/usr/bin/python3
import pickle
import argparse

from typing import Dict, List, Tuple
from Tokenizer import tokenize_query
from QueryRefinement import expand_query, run_rocchio
from Searcher import search_query, calc_query_vector, calc_doc_vectors
from Types import *
import Config


def run_search(dict_file: str, postings_file: str, queries_file: str, results_file: str):
    """
    using the given dictionary file, postings file, and optionally 
    thesaurus pickle file, perform searching on the given queries 
    file and output the results to the results file
    """
    print("running search on the queries...")

    # Read query file
    query_tokens: List[str] = []
    relevant_docs: List[DocId] = []
    with open(queries_file, "r") as qf:
        query = qf.readline()
        query_tokens = tokenize_query(query)
        while relevant_doc := qf.readline().strip():
            relevant_docs.append(int(relevant_doc))

    # if we are doing query expansion, we expand the query using
    # our thesaurus prebuilt from a legal text corpus
    if Config.RUN_QUERY_EXPANSION:
        with open(Config.THESAURUS_FILENAME, "rb") as tf:
            thesaurus = pickle.load(tf)
        query_tokens = expand_query(query_tokens, thesaurus)

    # we need to tag our query tokens with the zones
    # temp solution:
    query_tokens = ["content@" + tok for tok in query_tokens]

    dct: Dict[Term, Dict[DocId, List[TermPos]]]
    docs_len: Dict[DocId, DocLength]
    champion_dct: Dict[DocId, List[Tuple[Term, TermWeight]]]

    with open(dict_file, 'rb') as df,\
         open(Config.LENGTHS_FILE, 'rb') as lf,\
         open(Config.CHAMPION_FILE, "rb") as cf:
        dct = pickle.load(df)
        docs_len = pickle.load(lf)
        champion_dct = pickle.load(cf)

    search_output: List[DocId]
    search_output = search_query(query_tokens,
                                 dct,
                                 docs_len,
                                 postings_file,
                                 relevant_docs,
                                 champion_dct)
    
    output = " ".join(map(str, search_output))
    print(output, relevant_docs)
    with open(results_file, "w") as rf:
        rf.write(output)


# python3 search.py -d dictionary.txt -p postings.txt -q queries/q1.txt -o results.txt
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-d', dest='dictionary_file', required=True)
    arg_parser.add_argument('-p', dest='postings_file', required=True)
    arg_parser.add_argument('-q', dest='queries_file', required=True)
    arg_parser.add_argument('-o', dest='output_file', required=True)
    args = arg_parser.parse_args()

    run_search(args.dictionary_file, args.postings_file, args.queries_file, args.output_file)
