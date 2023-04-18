#!/usr/bin/python3
from typing import List, Dict, Tuple, Set
from Types import *
from Tokenizer import clean_query_token

# QUERY REFINEMENT
# Includes both query expansion and relevance feedback


def calc_centroid(champion_dct: Dict[DocId, List[Tuple[Term, TermWeight]]],
                  in_query_relevant_docs: List[DocId]) -> Vector:
    """
    Calculates the centroid of the relevant documents based on term weights.
    :param champion_dct: Dictionary of doc ID to list of tuples e.g [(Term, TermWeight), ....]
    :param in_query_relevant_docs: List of identified (relevant) Doc IDs
    :return: centroid 
    """
    centroid: Vector = {}

    for relevant_doc_id in in_query_relevant_docs:
        if relevant_doc_id not in champion_dct:
            continue
        term_weights = champion_dct[relevant_doc_id]
        for (term, weight) in term_weights:
            centroid[term] = centroid.get(term, 0) + weight

    for term in centroid.keys():
        centroid[term] /= len(in_query_relevant_docs)

    return centroid


def run_rocchio(alpha: float,
                beta: float,
                champion_dct: Dict[DocId, List[Tuple[Term, TermWeight]]],
                in_query_relevant_docs: List[DocId],
                query_vector: Dict[Term, float]) -> Dict[Term, float]:
    """
    Implements Rocchio algo to update query vector based on provided relevant documents
    :param alpha: Alpha coefficient for Rocchio Algorithm (Original Query)
    :param beta: Beta coefficient for Rocchio Algorithm (Relevant Documents)
    :param champion_dct: List of Tuples e.g [(Term, TermWeight), ....]
    :param in_query_relevant_docs: List of identified (relevant) Doc IDs
    :param query_vector: Dict of token-score k-v pairs
    :return: Updated query_vector after rocchio
    """
    centroid = calc_centroid(champion_dct, in_query_relevant_docs)

    for term in centroid.keys():
        if term not in query_vector:
            modified_centroid_score = centroid[term] * beta
        else:
            modified_centroid_score = alpha * query_vector[term] + beta * query_vector[term]
        query_vector[term] = modified_centroid_score
    return query_vector


def expand_query(tokens: List[str],
                 thesaurus: Dict[str, Set[str]]) -> List[str]:
    """
    Expands a query token to include related terms using the given thesaurus.
    :param tokens: List of tokens
    :param thesaurus: Thesaurus in dictionary form, with both key and value pre-stemmed
    :return: A set of new tokens expanded from the input list
    """
    result = set()
    for token in tokens:
        result.add(token)
        for synonym in thesaurus.get(token, set()):
            result.add(synonym)
    return list(result)