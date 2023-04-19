#!/usr/bin/python3
import pickle
import argparse

from typing import List
from Tokenizer import tokenize_query
from QueryRefinement import expand_query
from Searcher import search_query, boolean_and
from Types import *
import Config


def run_search(dict_file: str, postings_file: str, queries_file: str, results_file: str):
    """
    using the given dictionary file, postings file, and optionally 
    thesaurus pickle file, perform searching on the given queries 
    file and output the results to the results file
    """
    print("running search on the queries...")

    pointer_dct: Dict[Term, int]
    docs_len: Dict[DocId, DocLength]
    champion_dct: Dict[DocId, List[Tuple[Term, TermWeight]]]

    with open(dict_file, 'rb') as df,\
            open(Config.LENGTHS_FILE, 'rb') as lf,\
            open(Config.CHAMPION_FILE, "rb") as cf:
        pointer_dct = pickle.load(df)
        docs_len = pickle.load(lf)
        champion_dct = pickle.load(cf)

    # Read query file
    relevant_docs: List[DocId] = []
    with open(queries_file, "r") as qf:
        query = qf.readline()
        while relevant_doc := qf.readline().strip():
            relevant_docs.append(int(relevant_doc))

    # Tokenize the query and handle case where it is a phrasal query
    # and boolean query
    query_tokens = tokenize_query(query)
    is_boolean_query = 'AND' in query_tokens
    subqueries = [
        subquery for subquery in query_tokens if not subquery == 'AND']
    print("Subqueries ", subqueries)
    print("is_boolean", is_boolean_query)

    if is_boolean_query:
        intermediate_search_outputs = []
        for subquery in subqueries:
            # "adjustment AND beating" AND "bye world"
            # we need to tag our query tokens with the zones
            # query_tokens = ["content@" + tok for tok in subquery]

            tags = ["content@", "section@", "parties@", "title@"]
            search_tokens = [tag + subquery for tag in tags]
            print("Search tokens:", search_tokens)
            _, score = search_query(search_tokens,
                                    pointer_dct,
                                    docs_len,
                                    postings_file,
                                    relevant_docs,
                                    champion_dct)
            # print("Curr search output", subquery, curr_search_output)

            # boolean_and
            if not score:  # early termination
                return []
            if intermediate_search_outputs:  # if not empty, intersect
                intermediate_search_outputs = boolean_and(
                    intermediate_search_outputs, score)
            else:
                intermediate_search_outputs += score
        print("Final search output", intermediate_search_outputs)
        search_output = intermediate_search_outputs
    else:
        # if we are doing query expansion, we expand the query using
        # our thesaurus prebuilt from a legal text corpus
        if Config.RUN_QUERY_EXPANSION:
            with open(Config.THESAURUS_FILENAME, "rb") as tf:
                thesaurus = pickle.load(tf)
            query_tokens = expand_query(query_tokens, thesaurus)

        # we need to tag our query tokens with the zones
        # temp solution:
        query_tokens = ["content@" + tok for tok in query_tokens]

        search_output: List[DocId]
        search_output, _ = search_query(query_tokens,
                                        pointer_dct,
                                        docs_len,
                                        postings_file,
                                        relevant_docs,
                                        champion_dct)

    output = " ".join(map(str, search_output))
    # print("Output", output)
    # print("Relevant docs", relevant_docs)
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

    run_search(args.dictionary_file, args.postings_file,
               args.queries_file, args.output_file)
