import logging
import asyncio
import websockets
import json
import game_logic
import utils

def parse_card(card_string):
    assert len(card_string) == 2
    assert card_string[0] in utils.RANKS_MAP.keys()
    assert card_string[1] in utils.ALL_SUITS
    return game_logic.Card(utils.RANKS_MAP[card_string[0]], card_string[1])

global next_player_id
global next_game_id
next_game_id = 10000
next_player_id = 10000

def get_player_id():
    global next_player_id
    old_id = next_player_id
    next_player_id+=1
    return old_id

def get_game_id():
    global next_game_id
    old_id = next_game_id
    next_game_id+=1
    return old_id

games = {}
players = set()
connected_clients = set()
id_to_client = {}
client_to_id = {}

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


def handle_client_request(websocket, req):
    req_json = json.loads(req)
    print(req_json)

    if 'type' not in req_json.keys():
        return {'type': 'err', 'message': 'Malformed json: missing type'}
    
    if req_json['type'] != 'connect' and 'body' not in req_json.keys():
        return {'type': 'err', 'message': 'Malformed json: missing body'}

    if req_json['type'] == 'connect':
        id = get_player_id()
        players.add(id)
        id_to_client[id] = websocket
        client_to_id[websocket] = id
        return {'type': 'ack_connect', 'player_id': id}
    elif req_json['type'] == 'new_game':
        if 'player_id' not in req_json['body'].keys():
            return {'type': 'err_new_game', 'message': 'insufficient fields'}
        player_id = req_json['body']['player_id']
        if player_id not in players:
            return {'type': 'err_new_game', 'message': 'Failed to create game: user does not exist'}
        game_id = get_game_id()
        games[game_id] = Game(player_id)
        return {
            'type': 'ack_new_game',
            'player_id': player_id,
            'game_id': game_id,
        }
    elif req_json['type'] == 'join_game':
        if 'player_id' not in req_json['body'].keys() or 'game_id' not in req_json['body'].keys():
            return {'type': 'err_join_game', 'message': 'insufficient fields'}
        game_id = req_json['body']['game_id']
        player_id = req_json['body']['player_id']
        if game_id not in games.keys():
            return {'type': 'err_join_game', 'message': 'Failed to join game: game does not exist'}
        if games[game_id].state != 'created':
            return {'type': 'err_join_game', 'message': 'Failed to join game: game is already started'}
        else:
            games[game_id].connect(player_id)
            return {
                'type': 'ack_join_game',
                'player_id': player_id,
                'game_id': game_id
            }
    elif req_json['type'] == 'action':
        player_id = req_json['body']['player_id']
        game_id = req_json['body']['game_id']
        card_string = req_json['body']['card']
        pile_idx = int(req_json['body']['pile'])
        take_upcard = req_json['body']['take_upcard']
        if not all([a in req_json['body'].keys() for a in ['player_id', 'game_id', 'card', 'pile', 'take_upcard']]):
            return {'type': 'err_action', 'message': 'insufficient fields'}

        if game_id not in games.keys():
            return {'type': 'err_action', 'message': 'Game does not exist'}
        game = games[game_id]
        if player_id != game.p1 and player_id != game.p2:
            return {'type': 'err_action', 'message': 'Player is not in the game'}
        is_p1 = player_id == game.p1
        try: 
            game.game_state.player_act(parse_card(card_string), pile_idx, take_upcard, is_p1)
            return {
                'type': "ack_action",
                'player_id': player_id,
                'game_id': game_id,
            }
        except game_logic.IllegalPlayError as e:
            return {
                'type': 'err_action',
                'message': f'Illegal play. {e.message}'
            }
        
async def broadcast_to_game(json_to_broadcast, game_id):
    game = games[game_id]
    p1_websocket = id_to_client[game.p1]
    p2_websocket = id_to_client[game.p2]
    await p1_websocket.send(json_to_broadcast)
    await p2_websocket.send(json_to_broadcast)

async def send_to_game(p1_json, p2_json, game_id):
    game = games[game_id]
    p1_websocket = id_to_client[game.p1]
    p2_websocket = id_to_client[game.p2]
    await p1_websocket.send(p1_json)
    await p2_websocket.send(p2_json)

async def handle_after_ack(websocket, ack):
    if ack['type'] == 'ack_join_game':
        await broadcast_to_game(
            json.dumps({
                'type': 'game_start',
            }), 
            ack['game_id']
        )
        print('sending to p1')
        print(games[ack['game_id']].game_state.p1_json())
        print('sending to p2')
        print(games[ack['game_id']].game_state.p2_json())
        await send_to_game(
            json.dumps({
                'type': 'send_game_state',
                'game_state': games[ack['game_id']].game_state.p1_json()
            }), 
            json.dumps({
                'type': 'send_game_state',
                'game_state': games[ack['game_id']].game_state.p2_json()
            }), 
            ack['game_id']
        )

    if ack['type'] == 'ack_action':
        await send_to_game(
            json.dumps({
                'type': 'send_game_update',
                'update': games[ack['game_id']].game_state.get_last_update_p1()
            }), 
            json.dumps({
                'type': 'send_game_update',
                'update': games[ack['game_id']].game_state.get_last_update_p2()
            }), 
            ack['game_id']
        )

async def handler(websocket, path):
    connected_clients.add(websocket)
    try:
        while True:
            message = await websocket.recv()
            # try:
            ack =  handle_client_request(websocket, message)
            print(ack)
            await websocket.send(json.dumps(ack))
            await handle_after_ack(websocket, ack)
            # except Exception as e:
            #     print(e)
    except websockets.exceptions.ConnectionClosed:
        print(f'Client {client_to_id.get(websocket, " that never connected ")} exited')
    finally:
        connected_clients.remove(websocket)

start_server = websockets.serve(handler, "172.16.11.15", 8000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()