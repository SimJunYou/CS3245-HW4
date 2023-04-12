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

            title_token, title_doc_length = zoneMarker(title,"title")
            content_token, content_doc_length = zoneMarker(content,"content")
            date_token, date_doc_length = zoneMarker(date_posted,"date")
            court_token, court_doc_length = zoneMarker(court,"court")

            doc_length = title_doc_length + content_doc_length + date_doc_length + court_doc_length
            tokens = title_token + content_token + date_token + court_token

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

    #Read the provided stopwords file
    with open('stopwords.txt', 'r') as f:
        stopwords = set(f.read().split())


    tokens = nltk.tokenize.word_tokenize(doc_text)
    tokens = [STEMMER.stem(tok) for tok in tokens]
    def is_not_only_punct(tok): return any(char not in string.punctuation for char in tok)
    # Remove stopwords from the tokens and add delimiter for zones
    filtered_tokens = [word for word in tokens if word.lower() not in stopwords]
    zone_tokens = [zone + '@' + token  for token in filtered_tokens]
    return zone_tokens


def zoneMarker(data,zone):
    data = data.lower()
    tokens = tokenize(data,zone)
    doc_length = len(tokens)
    return tokens , doc_length


def clean_operand(operand: str) -> str:
    """
    Case-folds and stems a single operand (token).
    For use in Parser, when parsing queries.
    """
    return STEMMER.stem(operand.lower())
