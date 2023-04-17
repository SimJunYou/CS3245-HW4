from __future__ import annotations

import ctypes as ct

import csv
import nltk
import string

from Types import *
from typing import List, Set

STEMMER = nltk.stem.porter.PorterStemmer()
csv.field_size_limit(int(ct.c_ulong(-1).value // 2))  # found a fix from StackOverflow for field size too small


def make_doc_read_generator(in_file: str) -> TermInfoTupleGenerator:
    """
    Generator function for the next (term, term_pos, doc_length, doc_id) tuple.
    Call this function to make the generator first, then use next() to generate the next tuple.
    Yields (None, None, None, None) when done.
    :param in_file: The name of the input file
    :return: A generator object for the term information tuple (see above)
    """

    # read the provided stop words file ONCE and keep stop words in memory
    with open('stopwords.txt', 'r') as f:
        stopwords = set(f.read().split())

    with open(in_file, mode='r', encoding='utf-8', newline='') as doc:
        doc_reader = csv.reader(doc)
        for i, row in enumerate(doc_reader):
            if i == 0:
                continue  # we skip the first row (headers)
            doc_id, title, content, date_posted, court = row

            title_tokens = tokenize(title, "title", stopwords)
            content_tokens = tokenize(content, "content", stopwords)
            date_tokens = tokenize(date_posted, "date", stopwords)
            court_tokens = tokenize(court, "court", stopwords)

            tokens = title_tokens + content_tokens + date_tokens + court_tokens
            doc_length = len(tokens)

            print("progress:", i)

            # for this assignment, we can assume that document names are integers without exception
            # since we are using a generator, we only count the number of tokens once per file
            for term_pos, term in enumerate(tokens):
                yield term, term_pos, doc_length, int(doc_id)
    yield None, None, None, None


def tokenize(doc_text: str, zone: str, stop_words: Set[str]) -> List[str]:
    """
    Takes in document text and tokenizes.
    Also does post-tokenization cleaning like stemming.
    :param doc_text: The text to be tokenized
    :param zone: The zone the text is associated with
    :param stop_words: The set of stop words to be used
    :return: List of tokens
    """
    # case folding
    doc_text = doc_text.lower()

    # tokenize and stem
    tokens = nltk.tokenize.word_tokenize(doc_text)
    tokens = [STEMMER.stem(tok) for tok in tokens]

    # remove tokens that are purely punctuation
    def is_not_only_punct(tok): return any(char not in string.punctuation for char in tok)
    tokens = [tok for tok in tokens if is_not_only_punct(tok)]

    # remove stopwords from the tokens and add delimiter for zones
    tokens = [word for word in tokens if word not in stop_words]

    # each token will have the zone appended to the front using the @ symbol
    # for example, "title@token", "content@token"
    tokens = [zone + '@' + token for token in tokens]

    return tokens


def clean_operand(operand: str) -> str:
    """
    Case-folds and stems a single operand (token).
    For use in Parser, when parsing queries.
    :param operand: The token to be case-folded and stemmed
    :return: Case-folded and stemmed token
    """
    return STEMMER.stem(operand.lower())

def process_query(query: str) -> List[str]:
    """
    Takes in a string and performs tokenization, stemming and case-folding

    :param line: the string to process
    :return: a list of processed tokens
    """
    stemmer = nltk.stem.porter.PorterStemmer()
    tokens = nltk.word_tokenize(query)
    return [stemmer.stem(token.strip().casefold()) for token in tokens]