#!/usr/bin/python3
import sys
import getopt

from typing import *

def usage():
    print(
        "usage: "
        + sys.argv[0]
        + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"
    )

def run_search(dict_file: str, postings_file: str, queries_file: str, results_file: str):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print("running search on the queries...")

def expand_query(tokens: List[str]):
    with open("thesaurus.txt", "r") as f:
        thesaurus = eval(f.read())
    result = []
    for token in tokens:
        result.append(token)
        result += thesaurus.get(token, [])
    return result

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:p:q:o:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == "-d":
            dictionary_file = a
        elif o == "-p":
            postings_file = a
        elif o == "-q":
            file_of_queries = a
        elif o == "-o":
            file_of_output = a
        else:
            assert False, "unhandled option"

    # run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
    print(expand_query(["plaintiff"]))