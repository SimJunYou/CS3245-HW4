#!/usr/bin/python3
import pickle
import argparse
import json

from typing import *


def calc_centroid(relevant_docs_term_weights, in_query_relevant_docs):
    centroid = {}
    for relevant_doc_id in in_query_relevant_docs:
        term_weights = relevant_docs_term_weights[relevant_doc_id]

        for (term, weight) in term_weights:
            centroid[term] = centroid.get(term, 0) + weight

    for term, _ in centroid.items():
        centroid[term] /= len(in_query_relevant_docs)

    return centroid


# For this method, need to implement this in indexing
# Require top 10 tf-idf weights (corresponding to each term) for each doc id

# Derived from doc lengths
# Pseudo-code

# for every doc id in doc length
#  for every term in posting list
#     if doc id in postings dict[term]
#        calc tf-idf with normalisation
#        maintain a list of all these tf-idfs
# Get top 10 tf-idf weight in the form of list [term:tf-idf....]
# Store in as dictionary of doc id (key) : above list (value)
def run_rocchio(config, relevant_docs_term_weights, in_query_relevant_docs, query_vector):

    centroid = calc_centroid(
        relevant_docs_term_weights, in_query_relevant_docs)

    for term, _ in centroid.items():
        beta = config['beta']
        alpha = config['alpha']
        if term not in query_vector:
            modified_centroid_score = centroid[term] * beta
        else:
            modified_centroid_score = alpha * query_vector[term] + beta * query_vector[term]
        query_vector[term] = modified_centroid_score
    return query_vector


def run_search(dict_file: str, postings_file: str, queries_file: str,
               results_file: str, thesaurus_file: str):
    """
    using the given dictionary file, postings file, and optionally thesaurus pickle file,
    perform searching on the given queries file and output the results to a file
    """
    print("running search on the queries...")
    with open("config.json", "r") as f:
        config = json.load(f)

    # TODO: read query from file
    query_tokens = []

    # Expand query if a thesaurus is provided
    if thesaurus_file:
        with open(thesaurus_file, "rb") as f:
            thesaurus = pickle.load(f)
        # TODO: change hardcoded value to query_tokens
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


# python3 search.py -d dictionary.txt -p postings.txt -q queries/q1.txt -o results.txt -t thesaurus.pickle
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
