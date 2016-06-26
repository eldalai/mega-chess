import uuid

from pychess.chess import BoardFactory


class ManagerException(Exception):
    pass


class InvalidBoardIdException(ManagerException):
    pass


class InvalidTurnTokenException(ManagerException):
    pass


class Manager(object):
    '''
    Responsable to map board_id with board_id

    TODO: Store/Retrieve boards from DB
    '''

    def __init__(self):
        super(Manager, self).__init__()
        self.boards = {}
        self.turns = {}

    def _next_turn_token(self, board_id, previous_turn_token=None):
        if previous_turn_token and previous_turn_token in self.turns:
            del self.turns[previous_turn_token]
        turn_token = str(uuid.uuid4())
        self.turns[turn_token] = board_id
        return turn_token

    def challenge(self, white_player_id, black_player_id):
        board_id = self.create_board()
        turn_token = self._next_turn_token(board_id)
        return turn_token

    def create_board(self):
        board_id = str(uuid.uuid4())
        self.boards[board_id] = BoardFactory.with_pawns()
        return board_id

    def get_board_by_id(self, board_id):
        if board_id not in self.boards:
            raise InvalidBoardIdException()
        return self.boards[board_id]

    def get_board_id_by_turn_token(self, turn_token):
        if turn_token not in self.turns:
            raise InvalidTurnTokenException()
        return self.turns[turn_token]

    def move(self, board_id, from_row, from_col, to_row, to_col):
        return self.get_board_by_id(board_id).move(
            from_row,
            from_col,
            to_row,
            to_col,
        )

    def move_with_turn_token(self, turn_token, from_row, from_col, to_row, to_col):
        board_id = self.get_board_id_by_turn_token(turn_token)
        self.move(board_id, from_row, from_col, to_row, to_col)
        return self._next_turn_token(board_id, turn_token)
