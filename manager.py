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
FORCE_GAMEOVER_LIMIT = 25

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

ACTIVE = 'ACTIVE'
FINISH = 'FINISH'


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
        board_id=None,
    ):
        self.board = board
        self.white_username = white_username
        self.black_username = black_username
        self.turn_token = None
        self.white_score = white_score
        self.black_score = black_score
        self.move_left = move_left
        self.board_id = board_id

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

    @property
    def status(self):
        return ACTIVE if self.move_left > 0 else FINISH

    def serialize(self):
        return {
            'board': self.board.serialize(),
            'white_username': self.white_username,
            'black_username': self.black_username,
            'turn_token': self.turn_token,
            'white_score': self.white_score,
            'black_score': self.black_score,
            'move_left': self.move_left,
            'board_id': self.board_id,
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
        if(
            playing_board.move_left <= 0 or
            playing_board.white_score < INVALID_MOVE * FORCE_GAMEOVER_LIMIT or
            playing_board.black_score < INVALID_MOVE * FORCE_GAMEOVER_LIMIT
        ):
            self._save_board(board_id, playing_board)
            raise GameOverException()
        turn_token = str(uuid.uuid4())
        new_turn_token_key = self.get_turn_key(turn_token)
        playing_board.turn_token = turn_token
        self.redis_pool.set(new_turn_token_key, board_id)
        self._save_board(board_id, playing_board)
        actual_username = (
            playing_board.white_username
            if playing_board.board.actual_turn == WHITE
            else playing_board.black_username
        )
        self.log_board_data(
            board_id,
            'next_turn_token',
            {
                'turn_token': turn_token,
                'actual_turn': playing_board.board.actual_turn,
                'move_left': playing_board.move_left,
                'actual_username': actual_username,
            },
        )
        return (
            turn_token,
            actual_username,
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
        board_keys = self.redis_pool.keys(self.get_board_key(prefix + '*'))
        return (
            self.get_board_by_key(board_key)
            for board_key in board_keys
        )

    def get_board_log_key(self, board_id):
        return 'board-log:{}'.format(board_id)

    def get_board_log(self, board_id):
        board_log_key = self.get_board_log_key(board_id)
        return (
            ujson.loads(log)
            for log in self.redis_pool.lrange(board_log_key, 0, -1)
        )

    def log_board_data(self, board_id, event, data):
        board_log_key = self.get_board_log_key(board_id)
        self.redis_pool.rpush(
            board_log_key,
            ujson.dumps({
                'event': event,
                'data': data,
            }),
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
        self.log_board_data(
            board_id,
            'create_board',
            {
                'white_username': white_username,
                'black_username': black_username,
                'move_left': move_left,
            },
        )
        playing_board = PlayingBoard(
            board=BoardFactory.size_16(),
            white_username=white_username,
            black_username=black_username,
            move_left=move_left,
            board_id=board_id,
        )
        self._save_board(board_id, playing_board)
        return board_id

    def get_board_by_id(self, board_id):
        board_key = self.get_board_key(board_id)
        if not self.redis_pool.exists(board_key):
            raise InvalidBoardIdException()
        return self.get_board_by_key(board_key)

    def get_board_by_key(self, board_key):
        board_str = self.redis_pool.get(board_key)
        board = ujson.loads(board_str)
        if type(board_key) == bytes:
            board_key = board_key.decode('utf-8')
        board_id = board_key.split('board:')[1] if board_key else None
        playing_board = PlayingBoard(
            BoardFactory.deserialize(board['board']),
            board['white_username'],
            board['black_username'],
            board['move_left'],
            board['white_score'],
            board['black_score'],
            board_id=board_id,
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
            self.log_board_data(
                board_id,
                'add_score',
                {
                    'color': color,
                    'action': action,
                    'piece': piece,
                },
            )
        except Exception as e:
            self.log_board_data(
                board_id,
                'wrong_move',
                {
                    'color': color,
                    'exception': str(e),
                },
            )

            raise e
        finally:
            self.log_board_data(
                board_id,
                'score',
                {
                    'white_username': playing_board.white_username,
                    'black_username': playing_board.black_username,
                    'white_score': playing_board.white_score,
                    'black_score': playing_board.black_score,
                },
            )
            self._save_board(board_id, playing_board)

    def move_with_turn_token(self, turn_token, from_row, from_col, to_row, to_col):
        board_id = self.get_board_id_by_turn_token(turn_token)
        self.log_board_data(
            board_id,
            'move_with_turn_token',
            {
                'turn_token': turn_token,
                'from_row': from_row,
                'from_col': from_col,
                'to_row': to_row,
                'to_col': to_col,
            },
        )
        self.move(board_id, from_row, from_col, to_row, to_col)
        return self._next_turn_token(board_id, turn_token)

    def force_change_turn(self, board_id, turn_token):
        playing_board = self.get_board_by_id(board_id)
        playing_board.penalize_score(playing_board.board.actual_turn)
        self.log_board_data(
            board_id,
            'force_change_turn',
            {
                'turn_token': turn_token,
                'actual_turn': playing_board.board.actual_turn,
            },
        )
        self.log_board_data(
            board_id,
            'score',
            {
                'white_username': playing_board.white_username,
                'black_username': playing_board.black_username,
                'white_score': playing_board.white_score,
                'black_score': playing_board.black_score,
            },
        )
        if playing_board.board.actual_turn == WHITE:
            playing_board.board.actual_turn = BLACK
        else:
            playing_board.board.actual_turn = WHITE
        self._save_board(board_id, playing_board)
        return self._next_turn_token(board_id, turn_token)
