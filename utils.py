ALL_RANKS = [2,3,4,5,6,7,8,9,10,11,12,13,14]
RANKS_MAP = {
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8, '9': 9,
    'T': 10,
    'J': 11, 'Q': 12, 'K': 13, 'A': 14
}
ALL_SUITS = ['S', 'H', 'D', 'C']

HAND_STRENGTHS = ['STRAIGHT_FLUSH', 'QUADS', 'FULL_HOUSE', 'FLUSH', 'STRAIGHT', 'SET', 'TWO_PAIR', 'ONE_PAIR', 'HIGH_CARD']
HAND_STRENGTHS = HAND_STRENGTHS[::-1]

NUM_PILES = 5

def rank2str(rank):
    if rank == 10:
        return 'T'
    elif rank == 11:
        return 'J'
    elif rank == 12:
        return 'Q'
    elif rank == 13:
        return 'K'
    elif rank == 14:
        return 'A'
    return str(rank)