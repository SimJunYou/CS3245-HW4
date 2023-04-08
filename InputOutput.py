import sys
from typing import Dict, List, Mapping
from Types import *

import pickle
from math import floor, sqrt
from itertools import chain  # for flattening a nested list quickly


# === READING ===
# PostingReader class -> An interface for posting list reading.
# (All other methods removed in favor of this new class)


class PostingReader:
    """
    An interface for a posting list reading. Keeps the dictionary within itself, so accessing the posting list of any
    given term is as easy as ".seek_term('term')". Automatically grabs the doc frequency (the first entry) upon
    seeking. Has helper methods like .read_entry(), .is_done(), etc. Should be used with a context manager (i.e.
    'with' blocks) for automatic initialisation and closing of files.
    """

    def __init__(self, file, dct):
        self._filename: str = file
        self._dct: Dict[Term, int] = dct
        self._loc: int = 0
        self._done: bool = False  # flag for completing the reading of the given posting list

    def __enter__(self):
        self._f = open(self._filename, "r")
        return self

    def seek_term(self, term):
        """
        To be used right after entering the context manager!
        Seeks file to the desired term and returns the document frequency.
        """

        # we should be checking that terms are in dictionary in process_query
        assert term in self._dct, "Term not found in dictionary!"

        self._f.seek(self._dct[term], 0)

        # get document frequency
        doc_freq_str = char = ""
        while char != "$":
            doc_freq_str += char
            char = self._f.read(1)
        doc_freq = int(doc_freq_str)

        # since text files don't support relative seeks,
        # we need to store our previous location!
        # save location after reading the document frequency
        self._loc = self._f.tell()

        return doc_freq

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # parameters here are required by Python, we won't use them
        self._f.close()

    def read_entry(self):
        """
        Using the current position of the instance's file pointer,
        read the next entry in the posting list and return it as a tuple:
        >> (doc_id, term_freq)
        """
        # throw error if we're trying to read a completely read posting list
        assert not self._done, "Reading of posting list is already complete!"

        self._f.seek(self._loc, 0)

        entry = ""
        char = ""
        while char != "," and char != "|":
            entry += char
            char = self._f.read(1)
        if char == "|":
            self._done = True  # update flag if the posting list is done

        doc_id, term_freq = entry.split("*")

        self._loc = self._f.tell()

        # return a integer tuple
        return int(doc_id), int(term_freq)

    def is_done(self):
        return self._done


def unpickle_file(filename):
    """
    Just unpickles a file. Putting this here since I don't want to import pickle elsewhere!
    """
    return pickle.load(open(filename, "rb"))


# === WRITING ===
# write_block -> Writes in-memory dictionary into a block (dictionary + posting files)
# serialize_posting -> Turns a posting list into a formatted string


def write_block(dictionary: Dict[Term, Dict[DocId, List[TermPos]]],
                docs_len_dct: Dict[DocId, DocLength],
                out_dict: str,
                out_postings: str,
                write_skips: bool = False) -> None:
    """
    For each (term, posting list) pair in the dictionary...

    Each posting list is in the following format: [Dict[doc_id -> term_freq], doc_length]
    We extract the Dict and pass it to serialize_posting, which returns a string.
    The serialized posting list is written into the postings file.
    We count the number of characters written so far as cumulative_ptr.

    As each term is written, we write the (term -> cumulative_ptr) pair into final_dict.
    The cumulative_ptr can be used to directly grab a posting list from the postings file.

    The dictionary mapping doc_id to doc_length is made in the top-level index.py entry method,
    and is passed in here via docs_len_dct.

    The (final_dict, docs_len_dct) tuple is written into the dictionary file using pickle.
    :param dictionary: The dictionary of terms to posting lists
    :param docs_len_dct: The dictionary containing the length of documents
    :param out_dict: The desired name of the output dictionary file
    :param out_postings: The desired name of the output postings file
    :param write_skips: Whether to write skip pointers into the postings file
    :return: None
    """
    final_dict = dict()
    cumulative_ptr = 0

    with open(out_postings, "wb") as postings_fp:
        for term, posting_list in dictionary.items():
            posting_list_serialized: bytes
            posting_list_serialized = serialize_posting(posting_list, write_skips)

            # cumulative_ptr stores the number of bytes from the start of the file to the current entry
            # this lets us seek directly to the entry of the term we want
            final_dict[term] = cumulative_ptr
            cumulative_ptr += len(posting_list_serialized)
            postings_fp.write(posting_list_serialized)

    pickle.dump(final_dict, open(out_dict, "wb"))
    pickle.dump(
        docs_len_dct, open("lengths.txt", "wb")
    )  # FIXME: Don't hardcode file name?

    print(f"Wrote {len(dictionary)} terms into final files")


def serialize_posting(posting_list: Dict[DocId, List[TermPos]],
                      write_skips: bool) -> bytes:
    """
    Turns a posting list into a bytearray, and returns the bytearray.
    The byte format is:
        (freq)(num_docs)[doc_1][doc_2][...][doc_n]
    Each [doc_x] above is short for the following:
        (doc_id)(num_tp)(tp_1)(tp_2)(...)(tp_m)
    All items in the byte format, when fully expanded, are integers encoded using variable byte encoding.
    The term positions are encoded using delta encoding (before variable byte encoding).
    Delimiters are unnecessary as we encode the exact number of entries to expect.
    :param posting_list: The posting list to be serialized
    :param write_skips: Whether to write skip pointers into the postings file serialization (NOT IN USE)
    :returns: Bytearray representing the serialized posting list
    """

    # convert the dictionary into a list of tuples (doc_id, [term_pos])
    posting_list = list(posting_list.items())
    doc_freq = len(posting_list)

    # we take the 2nd element (term_freq) to sort by descending term frequency
    posting_list = sorted(posting_list, key=lambda x: -len(x[1]))

    # the prepare_entry method gives us a list of integers
    # by running it on each item in the posting list, we get a nested list of integers
    # we flatten that to get our final list of integers
    def flatten(arr): return list(chain.from_iterable(arr))
    prepared_entries: List[int]
    prepared_entries = flatten([prepare_entry(doc_id, term_pos_list) for doc_id, term_pos_list in posting_list])

    # add in the header as described in the docstring
    header = [doc_freq, len(posting_list)]
    final_entries = header + prepared_entries

    # variable-byte encode everything in the list of final entries, then return the bytearray
    serialized_list = map(variable_byte_encode, final_entries)
    return b"".join(serialized_list)  # flatten (using different method for an iterable of bytearrays)

    # # posting list should have at least 4 elements for skip pointers to be efficient
    # if write_skips and len(posting_list) >= 4:
    #     # calculate the last index which should contain a skip
    #     size = len(posting_list)
    #     skip_interval = floor(sqrt(size))
    #     last_skip = (size - 1) - skip_interval
    #     last_skip = last_skip - (last_skip % skip_interval)
    # else:
    #     # setting these to these values will stop skip pointers from being added
    #     last_skip = -1
    #     skip_interval = 1
    #
    # # since our skip pointers encode the number of characters to the next item with skip,
    # # we build the serialization from back to front, so we can count the number of
    # # characters between a later skip and an earlier skip more easily
    #
    # # if last_skip or skip_interval are set to 0, then skip pointers will not be added
    #
    # prev_skip_len = len(posting_list[-1])
    # for i, item in list(enumerate(posting_list))[::-1]:
    #     if i <= last_skip and i % skip_interval == 0:  # if current item has skip,
    #         output = f"{item}^{len(output) - prev_skip_len}," + output
    #         prev_skip_len += len(output) - prev_skip_len
    #     else:
    #         output = f"{item}," + output
    #     output = output[:-1] + "|"  # finally, replace ending comma with |
    #
    # output = f"{str(len(posting_list))}${output}"  # add in doc freq
    # return output


def prepare_entry(doc_id: DocId, term_pos_list: List[TermPos]) -> List[int]:
    """
    Performs delta encoding on the term positions list.
    Generates a list of integers following the following format:
        (doc_id)(num_tp)(tp_1)(tp_2)(...)(tp_m)
    :param doc_id: The document ID
    :param term_pos_list: The list of associated term positions
    :return: List of integers in the specified format
    """

    def delta_encode(lst: List[int]) -> List[int]:
        encoded = []
        prev = 0
        for curr in lst:
            encoded.append(curr - prev)
            prev = curr
        return encoded

    term_pos_list = delta_encode(term_pos_list)
    header = [doc_id, len(term_pos_list)]

    # we add in the number of term pos entries, so we know how long the list is
    return header + term_pos_list


def variable_byte_encode(num: int) -> bytes:
    """
    Follow the variable byte encoding taught in lecture!
    :param num: The number to be encoded
    :return: The encoded number in byte format
    """
    new_num = 0
    byte_count = 0
    while num > 0:
        byte_count += 1
        new_num <<= 8
        new_num |= (num & 0b1111111)
        num >>= 7
        if num > 0:
            new_num |= 0b1000_0000  # add continuation bit
    return new_num.to_bytes(byte_count, sys.byteorder)
