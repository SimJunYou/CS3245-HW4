#!/usr/bin/python3
import pickle
import argparse
import nltk
from typing import *

def run_search(dict_file: str, postings_file: str, queries_file: str, 
               results_file: str, thesaurus_file: str = ""):
    """
    using the given dictionary file, postings file, and optionally 
    thesaurus pickle file, perform searching on the given queries 
    file and output the results to the results file
    """
    print("running search on the queries...")

    query_tokens = []
    relevant_docs = []
    with open(queries_file, "r") as qf:
        query = qf.readline()
        query_tokens += process_query(query)
        while relevant_doc := qf.readline().strip():
            relevant_docs.append(relevant_doc)

    # Expand query if a thesaurus is provided
    if thesaurus_file:
        with open(thesaurus_file, "rb") as tf:
            thesaurus = pickle.load(tf)
        query_tokens = expand_query(query_tokens, thesaurus)
    
    print(query_tokens)

def process_query(query: str):
    stemmer = nltk.stem.porter.PorterStemmer()
    tokens = nltk.word_tokenize(query)
    return [stemmer.stem(token.lower()) for token in tokens]

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