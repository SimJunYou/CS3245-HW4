from InputOutput import PostingReader
from math import log10
from typing import Dict, List
from Types import *


def search_query(query: List[Token],
                 dictionary: Dict[Term, int],
                 docs_len_dct: Dict[DocId, DocLength],
                 postings_file: str) -> List[DocId]:
    """
    Using the PostingReader interface, process a given query by calculating
    scores for each document from its posting list, then return at most 10
    document IDs with the highest scores.
    :param query: The query as a list of tokens
    :param dictionary: A dictionary of terms to their positions in the postings list
    :param docs_len_dct: A dictionary of doc ID to doc length
    :param postings_file: The name of the postings list file
    :return: A list of relevant document IDs
    """
    all_query_terms = set(query)
    dictionary_terms = set(dictionary.keys())
    query_terms = all_query_terms & dictionary_terms
    N = len(docs_len_dct)

    # q_score_dct[term] = tf.idf_(term, query)
    q_score_dct: Dict[Term, float] = dict()

    # d_score_dct[term][doc_id] = tf.idf_(term, document)
    d_score_dct: Dict[Term, Dict[DocId, float]] = dict()

    with PostingReader(postings_file, dictionary) as pf:
        for query_term in query_terms:
            d_score_dct[query_term] = get_doc_tfidf_dict(query_term, pf)

        # finally, make it term -> doc_id _> tf.idf
        d_score_dct_inv: Dict[DocId, Dict[Term, float]]
        d_score_dct_inv = invert_nested_dict(d_score_dct)

        for query_term in query_terms:
            q_score_dct[query_term] = calc_query_tfidf(query_term, query, N, pf)

    # calculate the final scores for each document
    scores: List[Tuple[DocId, float]] = []
    for doc_id in d_score_dct_inv.keys():
        dot_prod = 0.
        for t in query_terms:
            d_score = d_score_dct_inv[doc_id].get(t, 0.)
            dot_prod += d_score * q_score_dct[t]
        score = dot_prod / docs_len_dct[doc_id]  # normalization
        scores.append((doc_id, score))

    # sort by ascending document ID first, then by descending score
    # since Python's sort is stable, we end up with a list sorted by
    # descending scores and tie-broken by ascending document IDs
    # return the top 10 in the list
    scores = sorted(scores, key=lambda x: x[0])
    scores = sorted(scores, key=lambda x: x[1], reverse=True)[:10]

    return [x[0] for x in scores]  # return doc IDs only!


def invert_nested_dict(original: Dict) -> Dict:
    """
    Simple utility function.
    If a dictionary is originally dct[a][b] = c, this function inverts it to become dct[b][a] = c instead.
    :param original: Original dictionary, should be nested by one layer
    :return: Inverted dictionary as described
    """
    flipped = dict()
    for key, nested_dct in original.items():
        for subkey, val in nested_dct.items():
            if subkey not in flipped:
                flipped[subkey] = {key: val}
            else:
                flipped[subkey][key] = val
    return flipped


def calc_query_tfidf(term: Term,
                     query: List[Token],
                     n: int,
                     pf: PostingReader) -> float:
    """
    Calculates the tf-idf weight of a term in a query.
    Takes in the posting file reader, N (total number of docs), and the list of tokens in the query.
    Returns a SINGLE tf-idf weight for that term and query.
    :param term: The term itself
    :param query: List of tokens representing the query
    :param n: Total number of documents
    :param pf: The postings file reader interface
    :return: The calculated weight
    """
    pf.seek_term(term)
    df = pf.get_doc_freq()  # document frequency of term
    idf = log10(n / df)  # inverse document freq of term

    term_freq = query.count(term)
    weight = (1 + log10(term_freq)) * idf

    return weight


def get_doc_tfidf_dict(term: str,
                       pf: PostingReader) -> Dict[DocId, float]:
    """
    Calculates the tf-idf weight of a term, for all docs listed in its
    posting list.
    Takes in the posting file reader and N (total number of docs).
    Returns a dictionary of doc ID -> tf-idf weight for that term/doc.
    :param term: The term itself
    :param pf: The postings file reader interface
    :return: The dictionary of calculated weights for each doc ID
    """
    pf.seek_term(term)

    weight_dct: Dict[DocId, float] = dict()
    while (pf.has_pos() and pf.get_num_docs_remaining() > 0) or (not pf.has_pos() and not pf.is_done()):
        if pf.has_pos():  # if positional indices are stored...
            doc_id, term_freq, _ = pf.read_next_doc()
        else:  # otherwise...
            doc_id, term_freq = pf.read_entry()
        # since we read directly from posting list,
        # term freq will never be 0, so we can ignore that case
        weight_dct[doc_id] = 1 + log10(term_freq)

    return weight_dct
