#!/usr/bin/python3
from __future__ import annotations

import getopt
import sys
import json
from math import log10
from typing import Dict, List, Tuple

# SELF-WRITTEN MODULES
from InputOutput import write_block
from Tokenizer import make_doc_read_generator
from Types import *
import Config


def build_index(in_file: str, out_dict: str, out_postings: str) -> None:
    """
    Build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print("indexing...")

    # we have a main dictionary mapping term and doc ID to term frequency
    # this is "main" because it directly mirrors the structure of our posting lists
    dictionary: Dict[Term, Dict[DocId, List[TermPos]]] = dict()

    # we want to capture all document IDs and each document's length
    # we can do that using a dictionary mapping doc_id to doc_length
    docs_len_dct: Dict[DocId, DocLength] = {}

    # we also want a more short-lived counter to count the frequency of each term for each document
    # term_freq_counter will get reset between documents, using current_doc to keep track
    term_freq_counter: Dict[Term, TermFreq] = dict()
    current_doc: Optional[DocId] = None

    # we use a generator to easily get the next term and relevant information from the given input dataset
    term_info_generator: TermInfoTupleGenerator = make_doc_read_generator(in_file, Config.STOP_WORDS_FILE)
    while True:
        generated = next(term_info_generator)

        # if we have run out of terms, we stop building index
        has_no_more_terms = all([x is None for x in generated])
        if has_no_more_terms:
            # we have one last document's length to calculate!
            # calc length and save to old doc's ID in docs_len_dct
            doc_length = 0
            for count in term_freq_counter.values():
                doc_length += (1 + log10(count)) ** 2
            docs_len_dct[current_doc] = doc_length ** 0.5
            break

        # otherwise, we proceed as normal!
        term, term_pos, doc_length, doc_id = generated

        # if we encounter a new document, update docs_len_dct with the calculated doc length and reset term_freq_counter
        if current_doc != doc_id:
            # calc length and save to old doc's ID in docs_len_dct
            doc_length = 0
            for count in term_freq_counter.values():
                doc_length += (1 + log10(count)) ** 2
            if current_doc is not None:
                docs_len_dct[current_doc] = doc_length ** 0.5
            # then, reset counter and update current_doc
            current_doc = doc_id
            term_freq_counter = dict()

        # count occurrences of each term in each document
        if term in term_freq_counter:
            term_freq_counter[term] += 1
        else:
            term_freq_counter[term] = 1

        # update our dictionary of term -> posting lists
        if term in dictionary:
            # posting_list contains a mapping of doc_id -> term_freq
            # one posting_list is held for each term
            posting_list = dictionary[term]
            if doc_id in posting_list:
                dictionary[term][doc_id] += [term_pos]
            else:
                dictionary[term][doc_id] = [term_pos]
        else:
            dictionary[term] = {doc_id: [term_pos]}

    # CALCULATE TOP K SIGNIFICANT TERMS FOR EACH DOCUMENT
    N = len(docs_len_dct)  # total number of docs

    top_K_terms_dct: Dict[DocId, List[Tuple[Term, TermWeight]]] = {}

    for doc_id in docs_len_dct:
        term_weight_list: List[Tuple[Term, TermWeight]] = []
        for term in dictionary:  
            if doc_id in dictionary[term]:
                if Config.WRITE_POS:
                    term_freq = len(dictionary[term][doc_id])
                else:
                    term_freq = dictionary[term][doc_id]
                doc_freq = len(dictionary[term])
                term_weight = (1 + log10(term_freq)) * log10(N / doc_freq)
                term_weight /= docs_len_dct[doc_id]  # normalization
                term_weight_list.append((term, term_weight))
        # sort by descending weights and keep top K
        term_weight_list = sorted(term_weight_list, key=lambda x: -x[1])[:Config.K]
        top_K_terms_dct[doc_id] = term_weight_list

    # we write the final posting list and dictionary to disk
    # write positional indices
    write_block(dictionary,
                docs_len_dct,
                top_K_terms_dct,
                out_dict,
                out_postings,
                Config.LENGTHS_FILE,
                Config.CHAMPION_FILE,
                Config.WRITE_POS)


def usage():
    print(
        "usage: "
        + sys.argv[0]
        + " -i directory-of-documents -d dictionary-file -p postings-file -l lengths-file"
    )


input_directory = output_file_dictionary = output_file_postings = output_file_lengths = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "i:d:p:")
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "-i":  # input directory
        input_directory = a
    elif o == "-d":  # dictionary file
        output_file_dictionary = a
    elif o == "-p":  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if (
        input_directory is None
        or output_file_postings is None
        or output_file_dictionary is None
):
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
