from InputOutput import PostingReader
from QueryRefinement import run_rocchio
from math import log10, sqrt
from typing import List
from Types import *


import Config


def search_query(query: List[Term],
                 dictionary: Dict[Term, int],
                 docs_len_dct: Dict[DocId, DocLength],
                 postings_file: str,
                 relevant_docs: List[DocId],
                 champion_dct: Dict[DocId, List[Tuple[Term, TermWeight]]]
                 ) -> List[DocId]:
    """
    Using the PostingReader interface, process a given query by calculating
    scores for each document from its posting list, then return at most 10
    document IDs with the highest scores.
    :param query: The query as a list of tokens
    :param dictionary: A dictionary of terms to their positions in the postings list
    :param docs_len_dct: A dictionary of doc ID to doc length
    :param postings_file: The name of the postings list file
    :param relevant_docs: The list of relevant document IDs (from the query file)
    :param champion_dct: The champion list as a dictionary
    :return: A list of relevant document IDs
    """
    all_query_terms = set(query)
    dictionary_terms = set(dictionary.keys())
    query_terms = list(all_query_terms & dictionary_terms)
    N = len(docs_len_dct)

    # CALCULATE QUERY VECTOR
    query_vector: Vector
    query_vector = calc_query_vector(postings_file, dictionary, query_terms, N)



    # REFINE QUERY VECTOR W/ ROCCHIO ALGO
    if Config.RUN_ROCCHIO:
        query_vector = run_rocchio(
            Config.ALPHA, Config.BETA, champion_dct, relevant_docs, query_vector)

    # CALCULATE DOCUMENT VECTOR
    doc_vector_dct: Dict[DocId, Vector]
    doc_vector_dct = calc_doc_vectors(postings_file, dictionary, query_terms)

    # Adding weights to individual zones
    for docID, vector in doc_vector_dct.items():
        for term in vector:
            if term.startswith("title"):
                vector[term]*=1.0
            elif term.startswith("content"):
                vector[term]*=0.8
            elif term.startswith("section"):
                vector[term]*=0.6
            elif term.startswith("parties"):
                vector[term]*=0.4               
            elif term.startswith("court"):
                vector[term]*=0.2

        doc_vector_dct[docID]=vector

    for term in query_vector:
        if term.startswith("title"):
            query_vector[term]*=1.0
        elif term.startswith("content"):
            query_vector[term]*=0.8
        elif term.startswith("section"):
            query_vector[term]*=0.6
        elif term.startswith("parties"):
            query_vector[term]*=0.4               
        elif term.startswith("court"):
            query_vector[term]*=0.2

    # calculate the final scores for each document
    doc_scores: List[Tuple[DocId, float]] = []
    for doc_id in doc_vector_dct.keys():
        dot_prod = 0.
        for t in query_terms:
            d_score = doc_vector_dct[doc_id].get(t, 0.)
            dot_prod += d_score * query_vector[t]
        score = dot_prod / docs_len_dct[doc_id]  # normalization
        doc_scores.append((doc_id, score))

    # sort by ascending document ID first, then by descending score
    # since Python's sort is stable, we end up with a list sorted by
    # descending scores and tie-broken by ascending document IDs
    # return the top 10 in the list
    doc_scores = sorted(doc_scores, key=lambda x: x[0])
    doc_scores = sorted(doc_scores, key=lambda x: x[1], reverse=True)

    return [x[0] for x in doc_scores]  # we only want to keep the doc IDs!


def calc_query_vector(postings_file: str,
                      dictionary: Dict[Term, int],
                      query_terms: List[str],
                      n: int) -> Vector:
    """
    Calculates a query vector based on given query terms.
    Query vector will be in the form of a dictionary of term -> weight.
    :param postings_file: The name of the postings file
    :param dictionary: The dictionary of term -> postings file pointer
    :param query_terms: The list of query terms
    :param n: The total number of documents
    :return: The query vector
    """
    query_vector: Vector = dict()

    with PostingReader(postings_file, dictionary) as pf:
        for term in query_terms:
            query_vector[term] = calc_query_tfidf(
                term, query_terms, n, pf)

    return query_vector

def boolean_and(listA: List[DocId], listB: List[DocId]):
    """
    And operation to find intersect between two lists WITHOUT skip pointers
    :param listA: list of IDs in first list
    :param listB: list of IDs in second list
    :return: list of IDs in both lists
    """
    return sorted(list(set(listA).intersection(set(listB))))

# List[Tuple[Term, TermWeight]


def generate_SP(postings: List[DocId]) -> List[Tuple[DocId, SkipPointer]]:
    """
    Turns list into list of tuples with second element being the skip pointer

    :param postings: list of document IDs e.g [1,2,3,4,5]
    :return: list of tuple e.g [(1,3),(2,None),(3,5), (4,None), (5, None)]
    """
    root_of_len = int(sqrt(len(postings)))
    for i in range(len(postings)):
        if (not i % root_of_len and i + root_of_len < len(postings)):
            postings[i] = (postings[i], i + root_of_len)
        else:
            postings[i] = (postings[i], None)
    return postings


def and_operator(listA: List[Tuple[DocId, SkipPointer]], listB: List[Tuple[DocId, SkipPointer]]) -> List[Tuple[DocId, SkipPointer]]:
    """
    And operation to find intersect between two lists
    :param listA: list of IDs in first list
    :param listB: list of IDs in second list
    :return: list of tuple (IDs, SP) in both lists 
    """
    res = []
    i = 0  # Pointer for listA
    j = 0  # Pointer for listB

    while (i < len(listA) and j < len(listB)):
        # If in both list, append
        if (listA[i][0] == listB[j][0]):
            res.append(listA[i][0])
            i += 1
            j += 1
        elif (listA[i][0] < listB[j][0]):
            # Use skip pointers if possible
            if (listA[i][1] is not None):
                skip_pointer = listA[i][1]
                if (listA[skip_pointer][0] <= listB[j][0]):
                    i = skip_pointer
                else:
                    i += 1
            else:
                i += 1

        # Case of listA[i][0] > listB[j][0]
        else:
            # Use skip pointers whenever possible
            if (listB[j][1] is not None):
                skip_pointer = listB[j][1]
                if (listB[skip_pointer][0] <= listA[i][0]):
                    j = skip_pointer
                else:
                    j += 1
            else:
                j += 1
    return generate_SP(res)


def getSubList(listOfTuple: List[Tuple[DocId, SkipPointer]], index: int) -> List[DocId]:
    """
    Extract list from list of tuple

    :param postings: list of tuple e.g [(1,3),(2,None),(3,5), (4,None), (5, None)]
    :param index: index at which u want to get the element from
    :return: list e.g [1,2,3,4,5]
    """
    if (not len(listOfTuple)):
        return []

    if (type(listOfTuple[0]) is not tuple):
        return listOfTuple

    return list(zip(*listOfTuple))[index]


def calc_doc_vectors(postings_file: str,
                     dictionary: Dict[Term, int],
                     query_terms: List[str]) -> Dict[DocId, Vector]:
    """
    Calculates a doc vectors based on given query terms.
    Document vectors will be in the form of a dictionary of (doc ID, term) -> weight.
    :param postings_file: The name of the postings file
    :param dictionary: The dictionary of term -> postings file pointer
    :param query_terms: The set of query terms
    :return: The document vector dictionary
    """
    doc_score_dct: Dict[Term, Dict[DocId, TermWeight]] = dict()
    doc_vector_dct: Dict[DocId, Vector]

    with PostingReader(postings_file, dictionary) as pf:
        for query_term in query_terms:
            doc_score_dct[query_term] = get_doc_tfidf_dict(query_term, pf)

    doc_vector_dct = invert_nested_dict(doc_score_dct)
    return doc_vector_dct


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
                     query_terms: List[Term],
                     n: int,
                     pf: PostingReader) -> float:
    """
    Calculates the tf-idf weight of a term in a query.
    Takes in the posting file reader, N (total number of docs), and the list of tokens in the query.
    Returns a SINGLE tf-idf weight for that term and query.
    :param term: The term itself
    :param query_terms: List of tokens representing the query
    :param n: Total number of documents
    :param pf: The postings file reader interface
    :return: The calculated weight
    """
    pf.seek_term(term)
    df = pf.get_doc_freq()  # document frequency of term
    idf = log10(n / df)  # inverse document freq of term

    term_freq = query_terms.count(term)
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
    while pf.get_num_docs_remaining() > 0:
        doc_id, term_freq, _ = pf.read_next_doc()
        # since we read directly from posting list,
        # term freq will never be 0, so we can ignore that case
        weight_dct[doc_id] = 1 + log10(term_freq)

    return weight_dct


