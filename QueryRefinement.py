#!/usr/bin/python3
from typing import List, Dict, Tuple, Set
from Types import *
from Tokenizer import clean_query_token

# QUERY REFINEMENT
# Includes both query expansion and relevance feedback

def calc_centroid(relevant_docs_term_weights: List[Tuple[Term, TermWeight]],
                  in_query_relevant_docs: List[DocId]) -> Dict[Term, float]:
    """
    Calculates the centroid of the relevant documents based on term weights.
    :param relevant_docs_term_weights: List of Tuples e.g [(Term, TermWeight), ....]
    :param in_query_relevant_docs: List of identified (relevant) Doc IDs
    :return: centroid 
    """
    centroid = {}
    for relevant_doc_id in in_query_relevant_docs:
        term_weights = relevant_docs_term_weights[relevant_doc_id]

        for (term, weight) in term_weights:
            centroid[term] = centroid.get(term, 0) + weight

    for term in centroid.keys():
        centroid[term] /= len(in_query_relevant_docs)

    return centroid


def run_rocchio(alpha: float,
                beta: float,
                relevant_docs_term_weights: List[Tuple[Term, TermWeight]],
                in_query_relevant_docs: List[DocId],
                query_vector: Dict[Term, float]) -> Dict[Term, float]:
    """
    Implements Rocchio algo to update query vector based on provided relevant documents
    :param alpha: Alpha coefficient for Rocchio Algorithm (Original Query)
    :param beta: Beta coefficient for Rocchio Algorithm (Relevant Documents)
    :param relevant_docs_term_weights: List of Tuples e.g [(Term, TermWeight), ....]
    :param in_query_relevant_docs: List of identified (relevant) Doc IDs
    :param query_vector: Dict of token-score k-v pairs
    :return: Updated query_vector after rocchio
    """
    centroid = calc_centroid(relevant_docs_term_weights, in_query_relevant_docs)

    for term in centroid.keys():
        if term not in query_vector:
            modified_centroid_score = centroid[term] * beta
        else:
            modified_centroid_score = alpha * query_vector[term] + beta * query_vector[term]
        query_vector[term] = modified_centroid_score
    return query_vector


def expand_query(tokens: List[str],
                 thesaurus: Dict[str, Set[str]]) -> Set[str]:
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
    return result