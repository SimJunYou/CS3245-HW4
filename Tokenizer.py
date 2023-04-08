from __future__ import annotations

import ctypes as ct

import csv
import nltk
import string

from Types import *

STEMMER = nltk.stem.porter.PorterStemmer()
csv.field_size_limit(int(ct.c_ulong(-1).value // 2))  # found a fix from StackOverflow for field size too small


def make_doc_read_generator(in_file: str) -> TermInfoTupleGenerator:
    """
    Generator function for the next (term, term_pos, doc_length, doc_id) tuple.
    Call this function to make the generator first, then use next() to generate the next tuple.
    Yields (None, None, None, None) when done.
    """
    with open(in_file, mode='r', encoding='utf-8', newline='') as doc:
        doc_reader = csv.reader(doc)
        for i, row in enumerate(doc_reader):
            if i == 0:
                continue  # we skip the first row (headers)
            doc_id, title, content, date_posted, court = row
            content = content.lower()
            tokens = tokenize(content)
            doc_length = len(tokens)
            print("progress:", i)

            # for this assignment, we can assume that document names are integers without exception
            # since we are using a generator, we only count the number of tokens once per file
            for term_pos, term in enumerate(tokens):
                yield term, term_pos, doc_length, int(doc_id)
    yield None, None, None, None


def tokenize(doc_text: str) -> list[str]:
    """
    Takes in document text and tokenizes.
    Also does post-tokenization cleaning like stemming.
    """
    tokens = nltk.tokenize.word_tokenize(doc_text)
    tokens = [STEMMER.stem(tok) for tok in tokens]
    def is_not_only_punct(tok): return any(char not in string.punctuation for char in tok)
    tokens = [tok for tok in tokens if is_not_only_punct(tok)]
    return tokens


def clean_operand(operand: str) -> str:
    """
    Case-folds and stems a single operand (token).
    For use in Parser, when parsing queries.
    """
    return STEMMER.stem(operand.lower())
