import random
import utils

def arbitrate_game(verdicts):
    pairs_to_win = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 2, 4]]
    is_p1_win = False
    is_p2_win = False
    for pair_to_win in pairs_to_win:
        if all([verdicts[i] == 1 for i in pair_to_win]):
            is_p1_win = True
        if all([verdicts[i] == 2 for i in pair_to_win]):
            is_p2_win = True    
    assert not (is_p1_win and is_p2_win)
    if is_p1_win:
        return 1
    if is_p2_win:
        return 2
    return 0

class IllegalPlayError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class Hand:
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def __repr__(self) -> str:
        return str(self.cards)
    
    def idx_of(self, card):
        idx = -1
        for i in range(len(self.cards)):
            if self.cards[i].equals(card):
                return i
        return idx
    
    def remove_idx(self, idx):
        self.cards.pop(idx)
        
    
class Pile:

    def __init__(self):
        self.p1_pile = []
        self.p2_pile = []
        self.verdict = 0 # 0 means undecided, 1 means p1, 2 means p2

    def p1_play(self, card):
        self.p1_pile.append(card)

    def p2_play(self, card):
        self.p2_pile.append(card)

    def __repr__(self) -> str:
        return f"P1 pile: {self.p1_pile.__repr__()}, P2 pile: {self.p2_pile.__repr__()}, verdict {self.verdict}"

class Card:

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return self.rank + self.suit
    
    def equals(self, other):
        return self.rank == other.rank and self.suit == other.suit

class Deck:

    def __init__(self):
        self.cards = []
        for rank in utils.ALL_RANKS:
            for suit in utils.ALL_SUITS:
                self.cards.append(Card(rank, suit))

        # random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop(0)

class GameState:

    def __init__(self):
        self.deck = Deck()
        self.p1_hand = Hand()
        self.p2_hand = Hand()
        self.is_p1_turn = True
        self.piles = [Pile() for i in range(5)]

        print('Deck at beginning is:', self.deck.cards)

        self.up_card = self.deck.draw()
        for i in range(5):
            self.p1_hand.add_card(self.deck.draw())
            self.p2_hand.add_card(self.deck.draw())

    def player_act(self, card, pile_idx:int, take_upcard:bool, is_p1: bool):
        if is_p1 != self.is_p1_turn:
            raise IllegalPlayError("Illegal play: not your turn")
        hand = self.p1_hand if is_p1 else self.p2_hand
        card_idx = hand.idx_of(card)
        if card_idx < 0:
            raise IllegalPlayError("Illegal play: don't have card")
        
        hand.remove_idx(card_idx)

        if is_p1:
            if len(self.piles[pile_idx].p1_pile) >= 5:
                raise IllegalPlayError('Pile is full')
            self.piles[pile_idx].p1_play(card)
        else:
            if len(self.piles[pile_idx].p2_pile) >= 5:
                raise IllegalPlayError('Pile is full')
            self.piles[pile_idx].p2_play(card)

        if take_upcard:
            hand.add_card(self.up_card)
            self.up_card = self.deck.draw()
        else:
            hand.add_card(self.deck.draw())

        self.is_p1_turn = not self.is_p1_turn

        verdicts = []
        verdict_updates = {}
        for i in range(5):
            verdict = self.arbitrate(i)
            if self.piles[i].verdict != verdict:
                self.piles[i].verdict = verdict
                verdict_updates[i] = verdict
            verdicts.append(verdict)
        game_verdict = arbitrate_game(verdicts)
        if game_verdict > 0:
            verdict_updates['GAME'] = game_verdict
        return verdict_updates
    
    def arbitrate(self, pile_idx):
        if len(self.piles[pile_idx].p1_pile) > len(self.piles[pile_idx].p2_pile):
            return 1
        if len(self.piles[pile_idx].p1_pile) < len(self.piles[pile_idx].p2_pile):
            return 2
        return 0

    def __repr__(self) -> str:
        return f"""
            GAME STATE
            DECK:
            {self.deck.cards.__repr__()}
            P1 HAND:
            {self.p1_hand}
            P2 HAND:
            {self.p2_hand}
            Up card: {self.up_card}
            PILE1: {self.piles[0]}
            PILE2: {self.piles[1]}
            PILE3: {self.piles[2]}
            PILE4: {self.piles[3]}
            PILE5: {self.piles[4]}
            turn: {1 if self.is_p1_turn else 2}
        """