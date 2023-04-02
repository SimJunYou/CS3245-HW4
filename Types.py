from __future__ import annotations
from typing import Optional
from _typeshed import SupportsNext

DocId = int
DocLength = float
Term = str
TermFreq = int

TermInfoTuple = tuple[Optional[str], Optional[int], Optional[int]]
TermInfoTupleGenerator = SupportsNext[TermInfoTuple]
