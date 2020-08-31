import uuid
import ujson

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

    def __init__(
        self,
        board,
        white_username,
        black_username,
        move_left,
        white_score=0,
        black_score=0,
    ):
        self.board = board
        self.white_username = white_username
        self.black_username = black_username
        self.turn_token = None
        self.white_score = white_score
        self.black_score = black_score
        self.move_left = move_left

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

    def serialize(self):
        return {
            'board': self.board.serialize(),
            'white_username': self.white_username,
            'black_username': self.black_username,
            'turn_token': self.turn_token,
            'white_score': self.white_score,
            'black_score': self.black_score,
            'move_left': self.move_left,
        }


class ChessManager(object):
    '''
    Responsable to turn_tokenmap board_id with board_id
    '''

    def __init__(self, redis_pool):
        self.redis_pool = redis_pool

    def get_turn_key(self, turn_token):
        return 'turn_bord:{}'.format(turn_token)

    def _next_turn_token(self, board_id, previous_turn_token=None):
        previous_turn_token_key = self.get_turn_key(previous_turn_token)
        if previous_turn_token and self.redis_pool.exists(previous_turn_token_key):
            self.redis_pool.delete(previous_turn_token_key)
        playing_board = self.get_board_by_id(board_id)
        playing_board.move_left -= 1
        if playing_board.move_left <= 0:
            raise GameOverException()
        turn_token = str(uuid.uuid4())
        new_turn_token_key = self.get_turn_key(turn_token)
        playing_board.turn_token = turn_token
        self.redis_pool.set(new_turn_token_key, board_id)
        self._save_board(board_id, playing_board)
        return (
            turn_token,
            (
                playing_board.white_username
                if playing_board.board.actual_turn == WHITE
                else playing_board.black_username
            ),
            playing_board.board.actual_turn,
            playing_board.board.get_simple(),
            playing_board.move_left,
        )

    def challenge(self, white_username, black_username, move_left):
        board_id = self.create_board(white_username, black_username, move_left)
        return board_id

    def challenge_accepted(self, board_id):
        return self._next_turn_token(board_id)

    def get_boards(self, prefix=''):
        return (
            board
            for board_id, board in self.boards.items()
            if board_id.startswith(prefix)
        )

    def get_board_key(self, board_id):
        return 'board:{}'.format(board_id)

    def _save_board(self, board_id, board):
        board_key = self.get_board_key(board_id)
        self.redis_pool.set(board_key, ujson.dumps(board.serialize()))

    def create_board(self, white_username, black_username, move_left, prefix=''):
        board_id = str(uuid.uuid4())
        if prefix:
            board_id = prefix + '::' + board_id
        playing_board = PlayingBoard(
            board=BoardFactory.size_16(),
            white_username=white_username,
            black_username=black_username,
            move_left=move_left,
        )
        self._save_board(board_id, playing_board)
        return board_id

    def get_board_by_id(self, board_id):
        board_key = self.get_board_key(board_id)
        if not self.redis_pool.exists(board_key):
            raise InvalidBoardIdException()
        board_str = self.redis_pool.get(board_key)
        board = ujson.loads(board_str)
        playing_board = PlayingBoard(
            BoardFactory.deserialize(board['board']),
            board['white_username'],
            board['black_username'],
            board['move_left'],
            board['white_score'],
            board['black_score'],
        )
        return playing_board

    def get_board_id_by_turn_token(self, turn_token):
        turn_token_key = self.get_turn_key(turn_token)
        if not self.redis_pool.exists(turn_token_key):
            raise InvalidTurnTokenException()
        return self.redis_pool.get(turn_token_key).decode('utf-8')

    def move(self, board_id, from_row, from_col, to_row, to_col):
        playing_board = self.get_board_by_id(board_id)
        color = playing_board.board.actual_turn
        try:
            action, piece = playing_board.move(
                from_row,
                from_col,
                to_row,
                to_col,
            )
            playing_board.add_score(color, action, piece)
        except Exception as e:
            playing_board.penalize_score(color)
            raise e
        finally:
            self._save_board(board_id, playing_board)

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
