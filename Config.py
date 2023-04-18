import json

with open("config.json", "r") as cf:
    config = json.load(cf)

    # CHAMPION LIST FILE
    K: int = config["champion_list"]["K"]
    CHAMPION_FILE: str = config["file_names"]["champion"]

    # LENGTHS FILE
    LENGTHS_FILE: str = config["file_names"]["lengths"]

    # STOP WORDS FILE
    STOP_WORDS_FILE: str = config["file_names"]["stop_words"]

    # POSITIONAL INDICES
    WRITE_POS: bool = config["write_pos_indices"]

    # QUERY EXPANSION
    RUN_QUERY_EXPANSION: bool = config["run_query_expansion"]
    THESAURUS_FILENAME: str = config["file_names"]["thesaurus"]

    # RELEVANCE FEEDBACK
    RUN_ROCCHIO: bool = config["run_rocchio"]
    ALPHA: float = config["rocchio"]["alpha"]
    BETA: float = config["rocchio"]["beta"]