# Mega Chess

Example of API calls:

register client1

sent from <MagicMock id='4463295440'>: {"action": "register", "data": {"username": "client1", "password": "12345678"} }
sent to <MagicMock id='4463295440'>: {'action': 'response_ok', 'data': {u'username': u'client1', u'password': u'12345678'}}

register client2

sent from <MagicMock id='4463443600'>: {"action": "register", "data": {"username": "client2", "password": "12345678"} }
sent to <MagicMock id='4463443600'>: {'action': 'response_ok', 'data': {u'username': u'client2', u'password': u'12345678'}}

login client1

sent from <MagicMock id='4463295440'>: {"action": "login", "data": {"username": "client1", "password": "12345678"} }
sent to <MagicMock id='4463295440'>: {'action': 'update_user_list', 'data': {'users_list': [u'client1']}}
sent to <MagicMock id='4463295440'>: {'action': 'response_ok', 'data': {u'username': u'client1', u'password': u'12345678'}}

login client2

sent from <MagicMock id='4463443600'>: {"action": "login", "data": {"username": "client2", "password": "12345678"} }
sent to <MagicMock id='4463443600'>: {'action': 'update_user_list', 'data': {'users_list': [u'client1', u'client2']}}
sent to <MagicMock id='4463443600'>: {'action': 'update_user_list', 'data': {'users_list': [u'client1', u'client2']}}
sent to <MagicMock id='4463443600'>: {'action': 'response_ok', 'data': {u'username': u'client2', u'password': u'12345678'}}

client1 challenge client2

sent from <MagicMock id='4463295440'>: {"action": "challenge", "data": {"username": "client2"} }
sent to <MagicMock id='4463443600'>: {'action': 'ask_challenge', 'data': {'username': u'client1', 'board_id': 'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742'}}
sent to <MagicMock id='4463295440'>: {'action': 'response_ok', 'data': {u'username': u'client2'}}

client2 accept challenge from client1

sent from <MagicMock id='4463443600'>: {"action": "accept_challenge", "data": {"board_id": "b65e2ac2-7cc5-4257-a6b0-cc656c9a1742"} }

client1 receive turn token and make first move

sent to <MagicMock id='4463295440'>: {'action': 'your_turn', 'data': {'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742', 'turn_token': 'f23fbbc2-5c11-4727-8ea7-60a8a147074b'}}
sent to <MagicMock id='4463443600'>: {'action': 'response_ok', 'data': {u'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742'}}
sent from <MagicMock id='4463295440'>: {"action": "move", "data": {"board_id": "b65e2ac2-7cc5-4257-a6b0-cc656c9a1742", "from_row": 6, "from_col": 3, "to_row": 5, "turn_token": "f23fbbc2-5c11-4727-8ea7-60a8a147074b", "to_col": 3}}
sent to <MagicMock id='4463295440'>: {'action': 'response_ok', 'data': {u'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742', u'from_row': 6, u'from_col': 3, u'to_row': 5, u'turn_token': u'f23fbbc2-5c11-4727-8ea7-60a8a147074b', u'to_col': 3}}


client2 receive turn token and make second move

sent to <MagicMock id='4463443600'>: {'action': 'your_turn', 'data': {'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742', 'turn_token': '249c439a-5bad-47ff-a39a-5b7118e68914'}}
sent from <MagicMock id='4463443600'>: {"action": "move", "data": {"board_id": "b65e2ac2-7cc5-4257-a6b0-cc656c9a1742", "from_row": 1, "from_col": 3, "to_row": 2, "turn_token": "249c439a-5bad-47ff-a39a-5b7118e68914", "to_col": 3}}
sent to <MagicMock id='4463443600'>: {'action': 'response_ok', 'data': {u'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742', u'from_row': 1, u'from_col': 3, u'to_row': 2, u'turn_token': u'249c439a-5bad-47ff-a39a-5b7118e68914', u'to_col': 3}}

client1 receive turn token ...

sent to <MagicMock id='4463295440'>: {'action': 'your_turn', 'data': {'board_id': u'b65e2ac2-7cc5-4257-a6b0-cc656c9a1742', 'turn_token': '32dcdab9-a4be-49ab-bae2-2a4aa53ef9ee'}}

list of movements
board status

errors?
final?
