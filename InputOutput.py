from __future__ import annotations

import sys
from typing import Dict, List, Tuple
from Types import *

import pickle
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
        self._dct: Dict[Term, int] = dct  # Term -> pointer
        self._loc: int = 0
        self._contains_pos: bool = False  # whether file contains pos. indices (set in __enter__ method)
        self._done: bool = False       # flag for completing the reading of the given posting list
        self._remaining_docs: int = 0  # keeps count of remaining docs in current posting list
        self._remaining_pos: int = 0   # keeps count of remaining term positions left in current doc
        self._doc_freq: DocFreq = 0    # records document frequency
        self._term_freq: TermFreq = 0  # records term frequency of current doc:term pair
        self._current_doc: DocId = 0   # records the id of the current doc
        self._curr_pos: TermPos = 0    # records the current term position (to undo gap encoding)

    def seek_term(self, term: str) -> None:
        """
        To be used right after entering the context manager!
        Seeks file to the desired term and returns the document frequency.
        :param term: The desired term
        """

        # we should be checking that terms are in dictionary in process_query
        assert term in self._dct, "Term not found in dictionary!"

        # reset the completion flag and seek to the posting list
        self._done = False
        self._f.seek(self._dct[term], 0)

        # get document frequency and update remaining count
        self._doc_freq = self.read_next_int()
        if self._contains_pos:
            # reading works slightly differently if the file contains pos. indices
            # we immediately read the first doc ID, so we start with -1 from remaining docs
            self._remaining_docs = self._doc_freq - 1

            # get current document ID and update
            curr_doc = self.read_next_int()
            self._current_doc = curr_doc

            # get term pos count for current doc and update remaining count
            term_pos_num = self.read_next_int()
            self._remaining_pos = term_pos_num  # this is for internal use (changes)
            self._term_freq = term_pos_num  # this is for data (does not change)
        else:
            # if the file does not contain pos. indices, we do not read immediately when seeking
            # so, we do not start with -1 from remaining docs
            self._remaining_docs = self._doc_freq

        # in our implementation, we save location after reading and re-seek each time
        self._loc = self._f.tell()

    def read_next_int(self) -> int:
        """
        Reads the next integer from the encoded file by decoding the variable byte encoding.
        :return: Next integer decoded from the file
        """
        buffer: int = int.from_bytes(self._f.read(1), sys.byteorder)
        collected_int: int = 0
        bits_added = 0
        while True:
            # inverse of the way we did variable byte encoding
            collected_int |= (buffer & 0b0111_1111) << bits_added
            bits_added += 7
            if buffer & 0b1000_0000:  # if continuation byte, we should continue to read
                buffer = int.from_bytes(self._f.read(1), sys.byteorder)
            else:
                break
        return collected_int

    def read_next_doc(self) -> Tuple[DocId, TermFreq] | Tuple[DocId, TermFreq, TermPos]:
        """
        Seek to the next document in the current posting list, discarding all read values in between.
        Returns the first set of values from the next document
        :return: Same tuple as read_entry would return
        """
        assert self._remaining_docs > 0, "No next document!"

        curr_doc: DocId = self._current_doc
        term_freq: TermFreq
        term_pos: TermPos
        if self._contains_pos:
            term_freq = term_pos = 0
            rem_docs = self._remaining_docs
            for _ in range(rem_docs):
                curr_doc, term_freq, term_pos = self.read_entry()
            return curr_doc, term_freq, term_pos
        else:
            curr_doc, term_freq = self.read_entry()
            return curr_doc, term_freq

    def read_entry(self) -> Tuple[DocId, TermFreq] | Tuple[DocId, TermFreq, TermPos]:
        """
        Using the current position of the instance's file pointer,
        read the next entry in the posting list and return it as a tuple:
        >> (doc_id, term_freq, term_pos) [if the file contains pos. indices]
        >> (doc_id, term_freq)           [otherwise]
        :return: Tuple of document ID, term frequency, and optionally term position
        """
        if self._contains_pos:
            return self._read_entry_with_pos()
        else:
            return self._read_entry_without_pos()

    def _read_entry_without_pos(self) -> Tuple[DocId, TermFreq]:
        """
        Using the current position of the instance's file pointer,
        read the next entry in the posting list and return it as a tuple:
        >> (doc_id, term_freq)
        :return: Tuple of document ID, term frequency
        """
        # throw error if we're trying to read a completely read posting list
        assert not self._done, "Reading of posting list is already complete!"

        self._f.seek(self._loc, 0)
        if self._remaining_docs > 0:
            self._remaining_docs -= 1
            if self._remaining_docs == 0:
                self._done = True
            self._current_doc = self.read_next_int()
            self._term_freq = self.read_next_int()

        self._loc = self._f.tell()  # update position
        return self._current_doc, self._term_freq

    def _read_entry_with_pos(self) -> Tuple[DocId, TermFreq, TermPos]:
        """
        Using the current position of the instance's file pointer,
        read the next entry in the posting list and return it as a tuple:
        >> (doc_id, term_freq, term_pos)
        :return: Tuple of document ID, term frequency, term position
        """
        # throw error if we're trying to read a completely read posting list
        assert not self._done, "Reading of posting list is already complete!"

        self._f.seek(self._loc, 0)

        if self._remaining_pos:  # if there are still term positions remaining,
            self._remaining_pos -= 1
            self._curr_pos += self.read_next_int()  # increment gap to get actual term pos
        else:  # else, we go to the next document
            self._remaining_docs -= 1
            # read the headers -> (doc_id)(num_tp), then read the first term pos
            self._current_doc = self.read_next_int()
            self._term_freq = self.read_next_int()
            self._remaining_pos = self._term_freq - 1  # we will read one term pos, so -1
            self._curr_pos = self.read_next_int()  # reset term pos at each document

        if self._remaining_pos <= 0 and self._remaining_docs <= 0:
            self._done = True

        self._loc = self._f.tell()  # update position
        return self._current_doc, self._term_freq, self._curr_pos

    def is_done(self):
        return self._done

    def get_doc_freq(self):
        return self._doc_freq

    def has_pos(self):
        return self._contains_pos

    def get_num_docs_remaining(self):
        return self._remaining_docs

    def get_stats(self):
        print("file name:\t", self._filename,
              "\nfile ptr:\t", self._loc,
              "\nhas pos:\t", self._contains_pos,
              "\nis done:\t", self._done,
              "\nrem docs:\t", self._remaining_docs,
              "\nrem pos:\t", self._remaining_pos,
              "\nterm freq:\t", self._term_freq,
              "\ncurr doc:\t", self._current_doc,
              "\ncurr pos:\t", self._curr_pos)

    def __enter__(self):
        """
        Upon initialization, read the header to figure out whether the postings list file contains positional indices.
        """
        self._f = open(self._filename, "rb")
        header = self._f.read(1)
        self._contains_pos = (header == b"\xFF")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        # parameters here are required by Python, we won't use them
        self._f.close()


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
                champion_dct: Dict[DocId, List[Tuple[Term, TermWeight]]],
                out_dict: str,
                out_postings: str,
                out_lengths: str,
                out_champion: str,
                write_pos: bool = False) -> None:
    """
    For each (term, posting list) pair in the dictionary...

    Each posting list is in the following format: [Dict[doc_id -> [term_pos1, ...]], doc_length]
    We extract the Dict and pass it to serialize_posting, which returns a bytearray.
    The serialized posting list is written into the postings file.
    We count the number of characters written so far as cumulative_ptr.

    As each term is written, we write the (term -> cumulative_ptr) pair into final_dict.
    The cumulative_ptr can be used to directly grab a posting list from the postings file.

    The dictionary mapping doc_id to doc_length is made in the top-level index.py entry method,
    and is passed in here via docs_len_dct.

    The (final_dict, docs_len_dct) tuple is written into the dictionary file using pickle.
    :param dictionary: The dictionary of terms to posting lists
    :param docs_len_dct: The dictionary containing the length of documents
    :param champion_dct: The dictionary containing the top K terms for each document
    :param out_dict: The desired name of the output dictionary file
    :param out_postings: The desired name of the output postings file
    :param out_lengths: The desired name of the output lengths file
    :param out_champion: The desired name of the output champions file
    :param write_pos: Whether to write positional indices into the postings file
    :return: None
    """
    final_dict = dict()

    with open(out_postings, "wb") as postings_fp:
        if write_pos:  # write postings file header
            postings_fp.write(b"\xFF")
        else:
            postings_fp.write(b"\x00")
        cumulative_ptr = 1  # we have already written 1 byte for the header

        for term, posting_list in dictionary.items():
            posting_list_serialized: bytes
            posting_list_serialized = serialize_posting(posting_list, write_pos)

            # cumulative_ptr stores the number of bytes from the start of the file to the current entry
            # this lets us seek directly to the entry of the term we want
            final_dict[term] = cumulative_ptr
            cumulative_ptr += len(posting_list_serialized)
            postings_fp.write(posting_list_serialized)

    pickle.dump(final_dict, open(out_dict, "wb"))
    pickle.dump(docs_len_dct, open(out_lengths, "wb"))
    pickle.dump(champion_dct, open(out_champion, "wb"))

    print(f"Wrote {len(dictionary)} terms into final files")


def serialize_posting(posting_list: Dict[DocId, List[TermPos]],
                      write_pos: bool) -> bytes:
    """
    Turns a posting list into a bytearray, and returns the bytearray.
    The byte format is:
        (doc_freq)[doc_1][doc_2][...][doc_n]
    If term positions are to be stored, each [doc_x] above is short for the following:
        (doc_id)(term_freq)(tp_1)(tp_2)(...)(tp_m)
    Otherwise, each [doc_x] above is for the following:
        (doc_id)(term_freq)
    All items in the byte format, when fully expanded, are integers encoded using variable byte encoding.
    The term positions are encoded using gap encoding (before variable byte encoding).
    Delimiters are unnecessary as we encode the exact number of entries to expect.
    :param posting_list: The posting list to be serialized
    :param write_pos: Whether to write positional indices into the postings file serialization
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

    if write_pos:
        nested_entries = [prepare_entry(doc_id, term_pos_list) for doc_id, term_pos_list in posting_list]
    else:
        nested_entries = [(doc_id, len(term_pos_list)) for doc_id, term_pos_list in posting_list]
        nested_entries = sorted(nested_entries, key=lambda x: -x[1])
    prepared_entries = flatten(nested_entries)

    # add in the header as described in the docstring
    header = [doc_freq]
    final_entries = header + prepared_entries

    # variable-byte encode everything in the list of final entries, then return the bytearray
    serialized_list = map(variable_byte_encode, final_entries)
    return b"".join(serialized_list)  # flatten (using different method for an iterable of bytearrays)


def prepare_entry(doc_id: DocId, term_pos_list: List[TermPos]) -> List[int]:
    """
    Performs gap encoding on the term positions list.
    Generates a list of integers following the following format:
        `(doc_id)(num_tp)(tp_1)(tp_2)(...)(tp_m)`
    :param doc_id: The document ID
    :param term_pos_list: The list of associated term positions
    :return: List of integers in the specified format
    """

    term_pos_list = gap_encode(term_pos_list)
    header = [doc_id, len(term_pos_list)]

    # we add in the number of term pos entries, so we know how long the list is
    return header + term_pos_list


def gap_encode(lst: List[int]) -> List[int]:
    """
    Perform gap encoding on the input list and return the encoded list as output.
    :param lst: The list to be gap encoded
    :return: The gap encoded list
    """
    encoded = []
    prev = 0
    for curr in lst:
        encoded.append(curr - prev)
        prev = curr
    return encoded


def variable_byte_encode(num: int) -> bytes:
    """
    Follow the variable byte encoding taught in lecture!
    Instead of having the 8th bit be 0 for continuation, we will set it to 1 for continuation.
    :param num: The number to be encoded
    :return: The encoded number in byte format
    """
    new_num = 0
    byte_count = 0
    while num > 0:
        new_part = (num & 0b1111111)
        num >>= 7
        if num > 0:
            new_part |= 0b1000_0000  # add continuation bit
        new_num |= new_part << (8 * byte_count)
        byte_count += 1
    return new_num.to_bytes(byte_count, sys.byteorder)
