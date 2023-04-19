# Configuration file for various parameters

# CHAMPION LIST FILE
K: int = 1000
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
ALPHA: float = 0.01
BETA: float = 10.0

# CONTENT PARSING
PARSING_CONFIG = {
    'NSW Court of Criminal Appeal': {
        'section': 'section, act',
        'num_words': 15,  # estimate number of words in a section
        'parties': 'parties, witness, victims, appellent, ms, mr',
        'parties_num_words': 3
    },
    'NSW Supreme Court': {
        'section': 'penalty, act, force',
        'num_words': 15,
        'parties': 'parties, witness, victims, appellent, ms, mr, offender, judgememt',
        'parties_num_words': 7
    },
    'CA Supreme Court': {
        'section': 'section, act, sect',
        'num_words': 10,
        'parties': 'respondent, present, defendant, prosecutrix, prosecutor, sir, plaintiff, named, acquainted',
        'parties_num_words': 3
    },
    'NSW District Court': {
        'section': 'section, act',
        'num_words': 15,
        'parties': 'parties, sir, mr, ms, witness, victims, appellent',
        'parties_num_words': 3
    },
    'SG High Court': {
        'section': 'section, act, case, number, crime, s, ss, CPC, penal, code',
        'num_words': 10,
        'parties': 'parties, judge, counsel, name(s), coram',
        'parties_num_words': 5
    },
    'High Court of Australia': {
        'section': 'act, code, statutes',
        'num_words': 10,
        'parties': 'parties, lawyer, high, court, australia, appellant, respondent, representation, intervener',
        'parties_num_words': 10
    },
    'Federal Court of Australia': {
        'section': 'legislation, section, act, catchwords',
        'num_words': 10,
        'parties': 'parties,judges,respondent,mr, ms',
        'parties_num_words': 5
    },
    'SG Court of Appeal': {
        'section': 'section, act, case, number, crime, s, ss, CPC, penal, code',
        'num_words': 10,
        'parties': 'parties, judge, counsel,coram',
        'parties_num_words': 5
    },
    'NSW Court of Appeal': {
        'section': 'section, act, charges, order',
        'num_words': 15,
        'parties': 'judgement, mr, ms, applicant, counsel, citation, complainant',
        'parties_num_words': 5
    },
    'UK Crown Court': {
        'section': 'convict, act, charges, honourable',
        'num_words': 10,
        'parties': 'mr, ms, applicant, counsel, victim, complainant, ‐v‐',
        'parties_num_words': 5
    },
    'SG District Court':{
        'section': 'section, act, case, number, crime, s, ss, CPC, penal, code',
        'num_words': 10,
        'parties': 'parties, judge, counsel, name(s), coram, prosecutor, you, ms, mr',
        'parties_num_words': 5
    },
    'UK Court of Appeal': {
        'section': 'apprehended, act, section',
        'num_words': 10,  # estimate number of words in a section
        'parties': 'between, witness, before, honour, appellent, ms, mr, ‐v‐, respondent',
        'parties_num_words': 4
    },
    'NSW Land and Environment Court': {
        'section': 'apprehended, act, section',
        'num_words': 10,  # estimate number of words in a section
        'parties': 'between, witness, before, honour, appellent, ms, mr, ‐v‐, respondent',
        'parties_num_words': 4
    }
}
