import random
import utils
from utils import HAND_STRENGTHS

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
        self.hand = None

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

    def eval(self):
        """
        returns current hand
        """
        if len(self.cards) != 5:
            raise Exception("Need 5 cards to evaluate")

        ranks = sorted([card.rank for card in self.cards])
        suits = [card.suit for card in self.cards]
        diffs = [ranks[i+1] - ranks[i] for i in range(len(ranks) - 1)]
        self.value_counts = {number: ranks.count(number) for number in set(ranks)}
        self.suit_counts = {number: suits.count(number) for number in set(suits)}


        if len(self.suit_counts.keys()) == 1:
            # must be flush or straight flush
            diffs = [ranks[i+1] - ranks[i] for i in range(len(ranks) - 1)]
            if diffs == [1,1,1,1] or diffs == [1,1,1,9]:
                self.hand =  "STRAIGHT_FLUSH"
            else:
                self.hand =  "FLUSH"
        elif len(self.value_counts.keys()) == 2 and max(self.value_counts.values()) == 4:
            self.hand = "QUADS"
        elif len(self.value_counts.keys()) == 2 and max(self.value_counts.values()) == 3:
            self.hand = "FULL_HOUSE"
        elif diffs == [1,1,1,1] or diffs == [9,1,1,1]:
            self.hand = "STRAIGHT"
        elif len(self.value_counts.keys()) == 3 and max(self.value_counts.values()) == 3:
            self.hand = "SET"
        elif len(self.value_counts.keys()) == 3 and max(self.value_counts.values()) == 2:
            self.hand = "TWO_PAIR"
        elif len(self.value_counts.keys()) == 4:
            self.hand = "ONE_PAIR"
        else:
            self.hand = "HIGH_CARD"

        return self.hand

    def eval_int(self):
        if self.hand is None:
            self.eval()
        self.hand_int = HAND_STRENGTHS.index(self.hand)
        return self.hand_int

    def get_primary_card(self):
        if self.hand is None:
            self.eval()
        
        if self.hand in {'STRAIGHT_FLUSH', 'FLUSH', 'STRAIGHT', 'HIGH_CARD'}:
            self.primary_card = max(self.value_counts.keys())
            if self.hand in {'STRAIGHT_FLUSH', 'STRAIGHT'} and self.primary_card == 14:
                self.primary_card = 5 if 13 not in self.value_counts.keys() else 14
        elif self.hand == 'TWO_PAIR':
            self.primary_card = max([card for card in self.value_counts.keys() if self.value_counts[card] == 2])
        else:
            self.primary_card = max(self.value_counts, key=self.value_counts.get)
        return self.primary_card

    def get_secondary_card(self):
        # can only be two pair or pair
        if self.hand == 'TWO_PAIR':
            self.secondary_card = max([card for card in self.value_counts.keys() if self.value_counts[card] == 2 and card != self.primary_card])
        elif self.hand in {'ONE_PAIR', 'HIGH_CARD'}:
            self.secondary_card = max([card for card in self.value_counts.keys() if card != self.primary_card])
        else:
            raise Exception("Shouldn't be calling secondary card on anything besides TWO_PAIR, PAIR_HIGH_CARD")

        return self.secondary_card

    def get_tertiary_card(self):
        self.tertiary_card = max([card for card in self.value_counts.keys() if card not in {self.primary_card, self.secondary_card}])
        return self.tertiary_card

    def get_quatenary_card(self):
        self.quatenary_card = max([card for card in self.value_counts.keys() if card not in {self.primary_card, self.secondary_card, self.tertiary_card}])
        return self.quatenary_card

    def get_senary_card(self):
        self.senary_card = max([card for card in self.value_counts.keys() if card not in {self.primary_card, self.secondary_card, self.tertiary_card, self.quatenary_card}])
        return self.senary_card
        

    def compare(self, other):
        """
        returns -2 if both are not completed
        returns 1 if self wins
        returns -1 if self loses
        return 0 if tie
        """
        if len(self.cards) != 5 and len(self.other) != 5:
            return -2

        for func1, func2 in zip([self.eval_int, self.get_primary_card, self.get_secondary_card, self.get_tertiary_card, self.get_quatenary_card, self.get_senary_card],
                                [other.eval_int, other.get_primary_card, other.get_secondary_card, other.get_tertiary_card, other.get_quatenary_card, other.get_senary_card]):
            val1 = func1()
            val2 = func2()
            if val1 > val2:
                return 1
            elif val1 < val2:
                return -1
            else:
                pass # cycle through
        return 0

    def get_rank_groups(self, cards):
        rank_groups = {}
        for card in cards:
            if card.rank not in rank_groups:
                rank_groups[card.rank] = []
            rank_groups[card.rank].append(card)
        return rank_groups

    def get_suit_groups(self, cards):
        suit_groups = {}
        for card in cards:
            if card.suit not in suit_groups:
                suit_groups[card.suit] = []
            suit_groups[card.suit].append(card)
        return suit_groups

    def greedy_best_hand(self, other, deck):
        pool = set(self.cards + other.cards + deck.cards)
        rank_groups = self.get_rank_groups(pool)
        suit_groups = self.get_suit_groups(pool)
        # Convert to sets for efficient lookups
        played_set = set(self.cards)

        # 1. Try Royal Flush / Straight Flush
        for suit, suited_cards in suit_groups.items():
            ranks = sorted(set(c.rank for c in suited_cards), reverse=True)
            # Check for straight flush
            for i in range(len(ranks) - 4):
                slice_ = ranks[i:i+5]
                if slice_[0] - slice_[-1] == 4:
                    hand = [Card(r, suit) for r in slice_ if Card(r, suit) in pool]
                    used = set(hand)
                    if played_set.issubset(used):
                        return hand
            # Special case: A-2-3-4-5
            if all(r in ranks for r in [14, 2, 3, 4, 5]):
                hand = [Card(r, suit) for r in [14, 5, 4, 3, 2] if Card(r, suit) in pool]
                if played_set.issubset(set(hand)):
                    return hand

        # 2. Four of a Kind
        for rank, group in rank_groups.items():
            if len(group) >= 4:
                hand = [c for c in group[:4]]
                kicker = max([Card(c.rank, c.suit) for c in pool if c.rank != rank], default=None)
                if kicker:
                    hand.append(kicker)
                if played_set.issubset(set(hand)):
                    return hand

        # 3. Full House
        trips = [c for c in rank_groups.values() if len(c) >= 3]
        trips = sorted(trips, key = lambda x: x[0].rank, reverse=True)
        pairs = [c for c in rank_groups.values() if len(c) >= 2]
        pairs = sorted(pairs, key = lambda x: x[0].rank, reverse=True)

        for t in trips:
            for p in pairs:
                if t[0].rank != p[0].rank:
                    hand = t[:3] + p[:2]
                    if played_set.issubset(set(hand)):
                        return hand

        # 4. Flush
        for suit, suited in suit_groups.items():
            if len(suited) >= 5:
                flush_hand = sorted(suited, reverse=True)[:5]
                if played_set.issubset(set(flush_hand)):
                    return [Card(r, suit) for r, suit in flush_hand]

        # 5. Straight
        all_ranks = sorted(set(card.rank for card in pool), reverse=True)
        for i in range(len(all_ranks) - 4):
            slice_ = all_ranks[i:i+5]
            if slice_[0] - slice_[-1] == 4:
                straight = []
                for r in slice_:
                    cards_with_rank = [card for card in pool if card.rank == r]
                    if cards_with_rank:
                        if r in [card.rank for card in played_set]:
                            straight.append([card for card in played_set if card.rank == r][0])
                        else:
                            straight.append(cards_with_rank[0])
                if played_set.issubset(set(straight)):
                    return straight
        # Special case A-2-3-4-5
        if all(r in all_ranks for r in [14, 2, 3, 4, 5]):
            straight = []
            for r in [14, 5, 4, 3, 2]:
                cards_with_rank = [card for card in pool if card.rank == r]
                if cards_with_rank:
                    if r in [card.rank for card in played_set]:
                        straight.append([card for card in played_set if card.rank == r][0])
                    else:
                        straight.append(cards_with_rank[0])
            if played_set.issubset(set(straight)):
                return straight

        # 6. Three of a Kind
        for group in rank_groups.values():
            if len(group) >= 3:
                hand = group[:3]
                kickers = sorted([c for c in pool if c.rank != group[0].rank], reverse=True)[:2]
                hand += kickers
                if played_set.issubset(set(hand)):
                    return hand

        # 7. Two Pair
        pairs = [g for g in rank_groups.values() if len(g) >= 2]
        pairs = sorted(pairs, key = lambda x: x[0].rank, reverse=True)
        if len(pairs) >= 2:
            p1, p2 = pairs[:2]
            hand = p1[:2] + p2[:2]
            kicker = max([c for c in pool if c.rank != p1[0].rank and c.rank != p2[0].rank], default=None)
            if kicker:
                hand.append(kicker)
            if played_set.issubset(set(hand)):
                print("HERE2")
                return hand

        # 8. One Pair
        if len(pairs) >= 1:
            hand = list(played_set)
            kickers = sorted([c for c in pool if c.rank != group[0].rank and c not in hand], reverse=True)[:5-len(hand)]
            hand += kickers
            if played_set.issubset(set(hand)):
                return hand

        # 9. High Card
        hand = played_set
        rest = sorted([c for c in pool if c not in hand], reverse=True)[:5-len(hand)]
        hand += rest
        if played_set.issubset(set(hand)):
            return [Card(r, suit) for r, suit in hand]

        return "Invalid", []


    def json(self):
        return [c.__repr__() for c in self.cards]
        
    
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

    def json(self):
        return {
            'p1': [card.__repr__() for card in self.p1_pile],
            'p2': [card.__repr__() for card in self.p2_pile],
            'verdict': self.verdict,
        }

class Card:

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f'{self.rank}{self.suit}'
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __lt__(self, other):
        return self.rank < other.rank
    
    def __gt__(self, other):
        return self.rank > other.rank

    def compare(self, other):
        if self.rank > other.rank:
            return 1
        elif self.rank < other.rank:
            return -1
        else:
            return 0

    def __hash__(self):
        return hash(str(self))

class Deck:

    def __init__(self):
        self.cards = []
        for rank in utils.ALL_RANKS:
            for suit in utils.ALL_SUITS:
                self.cards.append(Card(rank, suit))

        # random.shuffle(self.cards)

    def draw(self, card=None):
        if card is None:
            return self.cards.pop(0)
        return self.cards.remove(card)

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
        
        self.last_update_p1 = None
        self.last_update_p2 = None
        self.over = False
        self.winner = 0

    def player_act(self, card, pile_idx:int, take_upcard:bool, is_p1: bool):
        if self.over:
            raise IllegalPlayError('Illegal play: game is over')
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

        drawn_card = None
        if take_upcard:
            drawn_card = self.up_card
            self.up_card = self.deck.draw()
        else:
            drawn_card = self.deck.draw()
            hand.add_card(drawn_card)
        hand.add_card(drawn_card)

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
            self.over = True
            self.winner = game_verdict
        
        shared_update = {
            'verdict_updates': verdict_updates,
            'up_card': self.up_card,
            'pile_idx': pile_idx,
            'piles': self.piles[pile_idx].json(),
        }
        self.last_update_p1 = shared_update.copy()
        self.last_update_p2 = shared_update.copy()
        if is_p1:
            self.last_update_p1['remove_card'] = card
            self.last_update_p1['add_card'] = drawn_card
        else:
            self.last_update_p2['remove_card'] = card
            self.last_update_p2['add_card'] = drawn_card
    
    def arbitrate(self, pile_idx):
        """
        return -2 if non deterministic
        return 1 if p1_pile wins
        return -1 if p2_pile wins
        return 0 if tie
        """

        if len(self.piles[pile_idx].p1_pile) != 5 and len(self.piles[pile_idx].p2_pile) != 5:
            return -2
        elif len(self.piles[pile_idx].p1_pile) == 5 and len(self.piles[pile_idx].p2_pile) == 5:
            pass

        hand1 = self.piles[pile_idx].p1_pile
        hand2 = self.piles[pile_idx].p2_pile
        best_hand1 = hand1.greedy_best_hand(hand2, self.deck)
        best_hand2 = hand2.greedy_best_hand(hand2, self.deck)
        return best_hand1.compare(best_hand2)

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
    
    def p1_json(self):
        result = {
            'hand': self.p1_hand.json(), 
            'up_card': self.up_card.__repr__(),
            'is_my_turn': self.is_p1_turn,
            'player': 1,
        }
        for idx in range(5):
            result[f'pile{idx}'] = self.piles[idx].json() 
        return result
   
    def p2_json(self):
        result = {
            'hand': self.p2_hand.json(), 
            'up_card': self.up_card.__repr__(),
            'is_my_turn': not self.is_p1_turn,
            'player': 2,
        } 
        for idx in range(5):
            result[f'pile{idx}'] = self.piles[idx].json() 
        return result
      
    def last_update_p1(self):
        return self.last_update_p1

    def last_update_p2(self):
        return self.last_update_p2