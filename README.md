# Mega Chess

ClientA -> register(usuario, password)
ClientB -> register(usuario, password)

ClientA -> login(usuario, [password])
Server -> user_list() -> ClientA
ClientB -> login(usuario, [password])
Server -> user_list() -> ClientA, ClientB

ClientA  -> challenge(ClientB)
Server   -> ask_challenge(board_token) -> ClientB
ClientB  -> accept_challenge(board_token)

Server   -> your_turn(board_id, color, turn_token, timeout) -> ClientA
ClientA  -> move(turn_token, from_row, from_col, to_row, to_col) -> Server

Server  -> your_turn(board_id, color, turn_token, timeout) -> ClientB
ClientB -> move(turn_token, from_row, from_col, to_row, to_col, {previous_move}) -> Server

list of movements
board status

errors?
final?
