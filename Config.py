# Configuration file for various parameters

# CHAMPION LIST FILE
K: int = 10
CHAMPION_FILE: str = "champion.txt"

# LENGTHS FILE
LENGTHS_FILE: str = "lengths.txt"

# STOP WORDS FILE
STOP_WORDS_FILE: str = "stopwords.txt"

# POSITIONAL INDICES
WRITE_POS: bool = True

# QUERY EXPANSION
RUN_QUERY_EXPANSION: bool = True
THESAURUS_FILENAME: str = "stemmed_thesaurus.pickle"

# RELEVANCE FEEDBACK
RUN_ROCCHIO: bool = True
ALPHA: float = 1.0
BETA: float = 0.75

# CONTENT PARSING
PARSING_CONFIG = {
    'NSW Court of Criminal Appeal': {
        'section': 'section, act, case, number, s, crime',
        'num_words': 10, # estimate number of words in a section
        'parties': 'parties, witnesses, victims, appel, ms, mr',
        'parties_num_words': 3
    },
    'NSW Supreme Court': {
        'section': 'section, act, case, number, s, crime',
        'num_words': 10,
        'parties': 'parties, witnesses, victims, appel, ms, mr, offend',
        'parties_num_words': 3
    },
    'CA Supreme Court': {
        'section': 'section, act, case, number',
        'num_words': 10,
        'parties': 'parties, defendant, present, sir, plaintiff',
        'parties_num_words': 3
    },
    'NSW District Court': {
        'section': 'section, act, case, number',
        'num_words': 10,
        'parties': 'parties, sir, mr',
        'parties_num_words': 3
    },
    'SG High Court': {
        'section': 'section, act, case, number, crime',
        'num_words': 10,
        'parties': 'parties, judge',
        'parties_num_words': 3
    },
    'High Court of Australia': {
        'section': 'section, act, case, number',
        'num_words': 10,
        'parties': 'parties, lawyer',
        'parties_num_words': 3
    },
    'Federal Court of Australia': {
        'section': 'section, act, case, number',
        'num_words': 10,
        'parties': 'parties',
        'parties_num_words': 3
    },
    'SG Court of Appeal  ': {
        'section': 'section, act, case, number',
        'num_words': 10,
        'parties': 'parties, judge, lawyer',
        'parties_num_words': 3
    }
}
