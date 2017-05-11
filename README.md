# Mega Chess

Mega Chess is variation of Chess designed to be played by computer programs using code

[![Build Status](https://travis-ci.org/megachess/mega-chess.svg?branch=master)](https://travis-ci.org/megachess/mega-chess)

## How to play

You can use any programming lenguage, you only need to use a web socket client in order to send the command to the server.

WebSocket url is:
wss://mega-chess.herokuapp.com/service

## Rules

Mega Chess is *like* a Chess

### Similar Rules to Chess

* Piece movements
* Turns

### Different Rules to Chess

* Board is 16 x 16: For each piece in standard chess, you have 4 pieces
* Timeout: If you don't move in 10 seconds, you lose your turn
* No castle
* Promote: You promote automatically to queens when you pawns get the middle of the board
* Points:
    You will get **-1** points if you try to do a wrong movement.
    If you do a right move, you will get:

    Pawn: 10
    Horse: 30
    Bishop: 40
    Rook: 60
    Queen: 70
    King: 100

    If you do a eat an opponent piece, you will get:

    Pawn: 100
    Horse: 300
    Bishop: 400
    Rook: 600
    Queen: 700
    King: 1000

* There is no *Check* to Kings. You can eat a King and the game continue
* End of game: The game will be over on movement number 100. The winner is the player with more points.

## Example of API calls

### register client1

* sent from **client 1**: {"action": "register", "data": {"username": "client1", "password": "12345678"} }
* sent to **client 1**: {'action': 'response_ok', 'data': {u'username': u'client1', u'password': u'12345678'}}

### register client2

* sent from **client 2**: {"action": "register", "data": {"username": "client2", "password": "12345678"} }
* sent to **client 2**: {'action': 'response_ok', 'data': {u'username': u'client2', u'password': u'12345678'}}

### login client1

* sent from **client 1**: {"action": "login", "data": {"username": "client1", "password": "12345678"} }
* sent to **client 1**: {'action': 'update_user_list', 'data': {'users_list': [u'client1']}}
* sent to **client 1**: {'action': 'response_ok', 'data': {u'username': u'client1', u'password': u'12345678'}}

### login client2

* sent from **client 2**: {"action": "login", "data": {"username": "client2", "password": "12345678"} }
* sent to **client 2**: {'action': 'update_user_list', 'data': {'users_list': [u'client1', u'client2']}}
* sent to **client 2**: {'action': 'update_user_list', 'data': {'users_list': [u'client1', u'client2']}}
* sent to **client 2**: {'action': 'response_ok', 'data': {u'username': u'client2', u'password': u'12345678'}}

### client1 challenge client2

* sent from **client 1**: {"action": "challenge", "data": {"username": "client2"} }
* sent to **client 2**: {'action': 'ask_challenge', 'data': {'username': u'client1', 'board_id': 'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742'}}
* sent to **client 1**: {'action': 'response_ok', 'data': {u'username': u'client2'}}

### client2 accept challenge from client1

* sent from **client 2**: {"action": "accept_challenge", "data": {"board_id": "b65e2ac2-7cc5-4257-a6b0-cc656c9a1742"} }

### client1 receive turn token and make first move

* sent to **client 1**: {'action': 'your_turn', 'data': {'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742', 'turn_token': 'f23fbbc2-5c11-4727-8ea7-60a8a147074b'}}
* sent to **client 2**: {'action': 'response_ok', 'data': {u'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742'}}
* sent from **client 1**: {"action": "move", "data": {"board_id": "b65e2ac2-7cc5-4257-a6b0-cc656c9a1742", "from_row": 6, "from_col": 3, "to_row": 5, "turn_token": "f23fbbc2-5c11-4727-8ea7-60a8a147074b", "to_col": 3}}
* sent to **client 1**: {'action': 'response_ok', 'data': {u'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742', u'from_row': 6, u'from_col': 3, u'to_row': 5, u'turn_token': u'f23fbbc2-5c11-4727-8ea7-60a8a147074b', u'to_col': 3}}


### client2 receive turn token and make second move

* sent to **client 2**: {'action': 'your_turn', 'data': {'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742', 'turn_token': '249c439a-5bad-47ff-a39a-5b7118e68914'}}
* sent from **client 2**: {"action": "move", "data": {"board_id": "b65e2ac2-7cc5-4257-a6b0-cc656c9a1742", "from_row": 1, "from_col": 3, "to_row": 2, "turn_token": "249c439a-5bad-47ff-a39a-5b7118e68914", "to_col": 3}}
* sent to **client 2**: {'action': 'response_ok', 'data': {u'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742', u'from_row': 1, u'from_col': 3, u'to_row': 2, u'turn_token': u'249c439a-5bad-47ff-a39a-5b7118e68914', u'to_col': 3}}

### client1 receive turn token ...

* sent to **client 1**: {'action': 'your_turn', 'data': {'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742', 'turn_token': '32dcdab9-a4be-49ab-bae2-2a4aa53ef9ee'}}

