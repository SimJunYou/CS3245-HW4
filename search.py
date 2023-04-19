#!/usr/bin/python3
import pickle
import argparse

from typing import List
from Tokenizer import tokenize_query
from QueryRefinement import expand_query, tag_query_with_zones, extract_date
from Searcher import search_query
from Types import *
import Config


def run_search(dict_file: str, postings_file: str, queries_file: str, results_file: str):
    """
    using the given dictionary file, postings file, and optionally 
    thesaurus pickle file, perform searching on the given queries 
    file and output the results to the results file
    """
    print("running search on the queries...")

    # READ UTILITY FILES
    pointer_dct: Dict[Term, int]
    docs_len: Dict[DocId, DocLength]
    champion_dct: Dict[DocId, List[Tuple[Term, TermWeight]]]

    with open(dict_file, 'rb') as df,\
         open(Config.LENGTHS_FILE, 'rb') as lf,\
         open(Config.CHAMPION_FILE, "rb") as cf:
        pointer_dct = pickle.load(df)
        docs_len = pickle.load(lf)
        champion_dct = pickle.load(cf)

    # READ QUERY FILE
    query_tokens: List[str]
    relevant_docs: List[DocId] = []
    with open(queries_file, "r") as qf:
        query = qf.readline()
        while relevant_doc := qf.readline().strip():
            relevant_docs.append(int(relevant_doc))

    # QUERY PROCESSING
    # extract a single date from the query, if it exists
    # otherwise, extracted_dates will be an empty list
    extracted_dates: List[str] = extract_date(query)

    # tokenize the query
    query_tokens: List[str] = tokenize_query(query)

    # handle case where it is a phrasal query and boolean query
    is_boolean_query = 'AND' in query_tokens
    subqueries = [
        subquery for subquery in query_tokens if not subquery == 'AND']
    print("is_boolean", is_boolean_query)
    print("Subqueries", subqueries)

    # HANDLE BOOLEAN QUERY
    if is_boolean_query:
        ...

    # HANDLE FREE TEXT QUERY
    else:
        print("Query tokens before expansion:", query_tokens)

        free_text = [tok for tok in query_tokens if ' ' not in tok]
        phrasal_queries = [tok for tok in query_tokens if ' ' in tok]

        # QUERY EXPANSION (only for free text queries)
        if Config.RUN_QUERY_EXPANSION:
            with open(Config.THESAURUS_FILENAME, "rb") as tf:
                thesaurus = pickle.load(tf)
            free_text = expand_query(free_text, thesaurus)

        # TAGGING QUERY WITH ZONES
        free_text = tag_query_with_zones(free_text)
        free_text += ["date@" + date for date in extracted_dates]

        for i in range(len(phrasal_queries)):
            phrasal_queries[i] = ' '.join(tag_query_with_zones(phrasal_queries[i].split()))
        query_tokens = free_text + phrasal_queries
        print("Query tokens after expansion:", query_tokens)

        # SEARCHING
        search_output: List[DocId]
        search_output = search_query(free_text,
                                     phrasal_queries,
                                     pointer_dct,
                                     docs_len,
                                     postings_file,
                                     relevant_docs,
                                     champion_dct)

    # true_pos = sum([rd in search_output for rd in relevant_docs])
    # precision = true_pos / len(search_output)
    # recall = true_pos / len(relevant_docs)
    # f2_score = 5 * (precision * recall) / (4*precision + recall)

    output = " ".join(map(str, search_output))
    print("Docs found:", len(search_output), "Relevant docs:", relevant_docs)
    # print("Positions of results:", [1+search_output.index(rd) for rd in relevant_docs])
    # print(f"Precision: {precision}, Recall: {recall}, F2: {f2_score}")
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
