from __future__ import annotations
from typing import Optional, Iterator, Tuple

DocId = int
DocLength = float
DocFreq = int
Term = str
TermFreq = int
TermPos = int
TermWeight = float
Token = str

TermInfoTuple = Tuple[Optional[str], Optional[int], Optional[int], Optional[int]]
TermInfoTupleGenerator = Iterator[TermInfoTuple]
