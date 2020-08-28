import logging
import uuid

from pychess.chess import (
    Bishop,
    BLACK,
    BoardFactory,
    Horse,
    King,
    Pawn,
    Queen,
    RESULT_MOVE,
    RESULT_EAT,
    RESULT_PROMOTE,
    Rook,
    WHITE,
)

INVALID_MOVE = 'invalid_move'
score_by_action = {
    RESULT_MOVE: 1,
    RESULT_EAT: 10,
    RESULT_PROMOTE: 50,
    INVALID_MOVE: -20,
}

score_by_piece = {
    Pawn.PIECE_LETTER: 10,
    Horse.PIECE_LETTER: 30,
    Bishop.PIECE_LETTER: 40,
    Rook.PIECE_LETTER: 60,
    Queen.PIECE_LETTER: 70,
    King.PIECE_LETTER: 100,
}


class ManagerException(Exception):
    pass


class InvalidBoardIdException(ManagerException):
    pass


class InvalidTurnTokenException(ManagerException):
    pass


class GameOverException(ManagerException):
    pass


class PlayingBoard(object):

    def __init__(self, board, white_username, black_username, total_moves):
        self.board = board
        self.white_username = white_username
        self.black_username = black_username
        self.turn_token = None
        self.white_score = 0
        self.black_score = 0
        self.move_left = total_moves

    def _apply_score(self, color, score):
        if color == WHITE:
            self.white_score += score
        else:
            self.black_score += score

    def penalize_score(self, color):
        self._apply_score(color, score_by_action[INVALID_MOVE])

    def add_score(self, color, action, piece):
        self._apply_score(color, score_by_action[action] * score_by_piece[piece])

    def move(self, from_row, from_col, to_row, to_col):
        return self.board.move(from_row, from_col, to_row, to_col)


class ChessManager(object):
    '''
    Responsable to turn_tokenmap board_id with board_id

    TODO: Store/Retrieve boards from DB
    '''

    def __init__(self):
        super(ChessManager, self).__init__()
        self.boards = {}
        self.turns = {}

    def _next_turn_token(self, board_id, previous_turn_token=None):
        if previous_turn_token and previous_turn_token in self.turns:
            del self.turns[previous_turn_token]
        board = self.get_board_by_id(board_id)
        board.move_left -= 1
        if board.move_left <= 0:
            raise GameOverException()
        turn_token = str(uuid.uuid4())
        board.turn_token = turn_token
        self.turns[turn_token] = board_id
        return (
            turn_token,
            board.white_username if board.board.actual_turn == WHITE else board.black_username,
            board.board.actual_turn,
            str(board.board),
            board.move_left,
        )

    def challenge(self, white_username, black_username, total_moves):
        board_id = self.create_board(white_username, black_username, total_moves)
        return board_id

    def challenge_accepted(self, board_id):
        return self._next_turn_token(board_id)

    def get_boards(self, prefix=''):
        return (
            board
            for board_id, board in self.boards.items()
            if board_id.startswith(prefix)
        )

    def create_board(self, white_username, black_username, total_moves, prefix=''):
        board_id = prefix + '::' + str(uuid.uuid4())
        self.boards[board_id] = PlayingBoard(
            board=BoardFactory.size_16(),
            white_username=white_username,
            black_username=black_username,
            total_moves=total_moves,
        )

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
        board = self.get_board_by_id(board_id)
        color = board.board.actual_turn
        try:
            action, piece = board.move(
                from_row,
                from_col,
                to_row,
                to_col,
            )
            board.add_score(color, action, piece)
        except Exception as e:
            board.penalize_score(color)
            raise e

    def move_with_turn_token(self, turn_token, from_row, from_col, to_row, to_col):
        board_id = self.get_board_id_by_turn_token(turn_token)
        self.move(board_id, from_row, from_col, to_row, to_col)
        return self._next_turn_token(board_id, turn_token)

    def force_change_turn(self, board_id, turn_token):
        board = self.get_board_by_id(board_id)
        board.penalize_score(board.board.actual_turn)
        if board.board.actual_turn == WHITE:
            board.board.actual_turn = BLACK
        else:
            board.board.actual_turn = WHITE
        return self._next_turn_token(board_id, turn_token)
