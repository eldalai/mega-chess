import ujson
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
    INVALID_MOVE: -1,
}

score_by_piece = {
    Pawn.PIECE_LETTER: 10,
    Horse.PIECE_LETTER: 30,
    Bishop.PIECE_LETTER: 40,
    Rook.PIECE_LETTER: 60,
    Queen.PIECE_LETTER: 70,
    King.PIECE_LETTER: 100,
}
TOTAL_GAME_TURNS = 100


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
        redis_pool,
        white_username,
        black_username,
        board_id=str(uuid.uuid4()),
        board=None,
        turn_token=None,
        white_score=0,
        black_score=0,
        turn_count=0,
    ):
        self.redis_pool = redis_pool
        self.white_username = white_username
        self.black_username = black_username
        self.board_id = board_id
        self.board = board if board else BoardFactory.size_16()
        self.turn_token = turn_token
        self.white_score = white_score
        self.black_score = black_score
        self.turn_count = turn_count
        self._save()

    def _apply_score(self, color, score):
        if color == WHITE:
            self.white_score += score
        else:
            self.black_score += score
        self._save()

    def penalize_score(self, color):
        self._apply_score(color, score_by_action[INVALID_MOVE])

    def add_score(self, color, action, piece):
        self._apply_score(color, score_by_action[action] * score_by_piece[piece])

    def next_turn(self):
        self.turn_count += 1
        if self.turn_count >= TOTAL_GAME_TURNS:
            self._save()
            raise GameOverException()
        self.turn_token = str(uuid.uuid4())
        self._save()
        return self.turn_token

    @property
    def winner(self):
        if self.black_score > self.white_score:
            return self.black_username
        elif self.black_score < self.white_score:
            return self.white_username
        return 'draw'

    @staticmethod
    def _board_id(board_id):
        return 'board:{}'.format(board_id)

    @staticmethod
    def recover(redis_pool, board_id):
        if not redis_pool.exists(PlayingBoard._board_id(board_id)):
            raise InvalidBoardIdException()

        board_string = self.redis_pool.get(self._user_id())
        board_dict = ujson.loads(board_string)
        board = PlayingBoard(
            redis_pool,
            board_dict['white_username'],
            board_dict['black_username'],
            board_dict['board_id'],
            BoardFactory.deserialize(board_dict['board']),
            board_dict['turn_token'],
            board_dict['white_score'],
            board_dict['black_score'],
            board_dict['turn_count'],
        )
        return board

    def _save(self):
        board_json = ujson.dumps({
            'board_id': self.board_id,
            'board': self.board.serialize(),
            'white_username': self.white_username,
            'black_username': self.black_username,
            'turn_token': self.turn_token,
            'white_score': self.white_score,
            'black_score': self.black_score,
            'turn_count': self.turn_count,
        })
        self.redis_pool.set(PlayingBoard._board_id(self.board_id), board_json)


class ChessManager(object):
    '''
    Responsable to turn_tokenmap board_id with board_id

    TODO: Store/Retrieve boards from DB
    '''

    def __init__(self, redis_pool):
        self.redis_pool = redis_pool
        self.boards = {}
        self.turns = {}

    def _next_turn_token(self, board_id, previous_turn_token=None):
        if previous_turn_token and previous_turn_token in self.turns:
            del self.turns[previous_turn_token]
        board = self.get_board_by_id(board_id)
        turn_token = board.next_turn()
        self.turns[turn_token] = board_id
        return (
            turn_token,
            board.white_username if board.board.actual_turn == WHITE else board.black_username,
            board.board.actual_turn,
            str(board.board),
        )

    def challenge(self, white_username, black_username):
        board_id = self.create_board(white_username, black_username)
        return board_id

    def challenge_accepted(self, board_id):
        return self._next_turn_token(board_id)

    def create_board(self, white_username, black_username):
        board = PlayingBoard(
            redis_pool=self.redis_pool,
            white_username=white_username,
            black_username=black_username,
        )
        self.boards[board.board_id] = board
        return board.board_id

    def get_board_by_id(self, board_id):
        if board_id not in self.boards:
            self.boards[board_id] = PlayingBoard.recover(self.redis_pool, board_id)
        return self.boards[board_id]

    def get_board_id_by_turn_token(self, turn_token):
        if turn_token not in self.turns:
            raise InvalidTurnTokenException()
        return self.turns[turn_token]

    def move(self, board_id, from_row, from_col, to_row, to_col):
        board = self.get_board_by_id(board_id)
        color = board.board.actual_turn
        try:
            action, piece = board.board.move(
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
