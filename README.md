# CS3245-HW4

## Project Design

### Indexing

Main entry point is `index.py`. Helper files are `InputOutput.py`, `Tokenizer.py`.

Indexing approach TBC, need to decide on how to approach positional indexing.

### Searching

TBC.

## Project style and setup

### Project setup

Use whatever CPython interpreter as long as you are on 3.8.10 and have NLTK (with `punkt` downloaded).
We can use external libraries if we package them with our code, but let's try not to.

### Code style

Let's keep things consistent!
* `snake_case` for variables and functions
* `PascalCase` for classes/objects and custom types

### Type hints

This project will probably get big and complicated with multiple people working on it,
so type hints
[[1]](https://peps.python.org/pep-0484/)
[[2]](https://docs.python.org/3.8/library/typing.html)
are encouraged. Add custom types to `Types.py` and import to whichever files need it.

Dictionaries and nested dictionaries are common, so we have common atomic values like `DocId` and `Term`
abstracted as custom types in `Types.py` to make dictionary types clearer. E.g., `Dict[DocId, DocFreq]`
rather than `Dict[int, int]`.

Since we are on Python 3.8.10, we will need `from __future__ import annotations` to get proper type hinting.

