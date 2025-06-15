import game_logic
import utils

def parse_card(card_string):
    assert len(card_string) == 2
    assert card_string[0] in utils.ALL_RANKS
    assert card_string[1] in utils.ALL_SUITS
    return game_logic.Card(card_string[0], card_string[1])


# Caller can 
# connect(void)
# connect(int)
# playCard(string)

# We will
# notifyCardRemove()
# notifyCardAdd()
# notifyVerdictUpdate()
# notifyGameOver()

games = {}
global id_next
id_next = 10000

class Game:

    def __init__(self, p1_id):
        self.state = 'created'
        self.p1 = p1_id
        self.p2 = None
        self.game_state = None

    def connect(self, p2_id):
        self.p2 = p2_id
        self.game_state = game_logic.GameState()
        self.state = 'connected'

def connect_first(player_id):
    global id_next
    games[id_next] = Game(player_id)
    old_id = id_next
    id_next+=1
    return old_id

def connect_second(id, player_id):
    assert id in games.keys()
    assert games[id].p1 != player_id
    games[id].connect(player_id)

def play_card(player_id, game_id, card_string, pile_idx, take_upcard):
    assert game_id in games.keys()
    game = games[game_id]
    assert player_id == game.p1 or player_id == game.p2
    is_p1 = player_id == game.p1
    try:
        verdict_updates = game.game_state.player_act(parse_card(card_string), pile_idx, take_upcard, is_p1)
        return verdict_updates
    except game_logic.IllegalPlayError as e:
        print(f'Illegal move. Message: {e.message}')

if __name__ == "__main__":
    game_id = connect_first(1)
    connect_second(game_id, 2)
    print(games[game_id].game_state)

    updates = play_card(1, game_id, 'AH', 1, True)
    print(updates)
    updates = play_card(2, game_id, 'KS', 2, False)
    print(updates)
    updates = play_card(1, game_id, 'KS', 0, False)
    updates = play_card(2, game_id, 'JS', 0, False)
    print(games[game_id].game_state)
    # print(updates)