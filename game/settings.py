'''

Imports

'''

from enum import Enum

'''

Constants

'''


class States(Enum):

    CREATED = 'Created'
    OPENED = 'Open'
    GENERATED = 'Generating'
    STARTED = 'Started'
    ENDED = 'Ended' 





# Inclusive
MAX_PLAYERS = 10
MIX_PLAYERS = 5
STARTING_ENERGY = 5


ALIGNMENT_MAPPING = {
    5: {
        'Mutineers': 2,
        'Bucaneers': 3
    },
    6: {
        'Mutineers': 2,
        'Bucaneers': 4
    },
    7: {
        'Mutineers': 3,
        'Bucaneers': 4
    },
    8: {
        'Mutineers': 3,
        'Bucaneers': 5
    },
    9: {
        'Mutineers': 4,
        'Bucaneers': 5
    },
    10: {
        'Mutineers': 4,
        'Bucaneers': 6
    }
}
