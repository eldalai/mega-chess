import unittest
from pychess.chess import (
    BLACK,
    WHITE,
    InvalidTurnException,
)

from manager import (
    InvalidBoardIdException,
    InvalidTurnTokenException,
    ChessManager,
)


class TestChessManager(unittest.TestCase):

    def setUp(self):
        super(TestChessManager, self).setUp()
        self.manager = ChessManager()
        self.board_id = self.manager.create_board(
            white_username='white',
            black_username='black',
        )

    def test_get_invalid_board(self):
        with self.assertRaises(InvalidBoardIdException):
            self.manager.get_board_by_id('hola-mundo')

    def test_create_board(self):
        board = self.manager.get_board_by_id(self.board_id)
        self.assertIsNotNone(board)
        self.assertEqual(board.board.actual_turn, WHITE)
        self.assertEqual(board.white_score, 0)
        self.assertEqual(board.black_score, 0)

    def test_invalid_move(self):
        with self.assertRaises(InvalidTurnException):
            self.manager.move(self.board_id, 2, 3, 3, 3)
        board = self.manager.get_board_by_id(self.board_id)
        self.assertIsNotNone(board)
        self.assertEqual(board.board.actual_turn, WHITE)
        self.assertEqual(board.white_score, -1)
        self.assertEqual(board.black_score, 0)

    def test_move(self):
        self.manager.move(self.board_id, 12, 3, 11, 3)
        board = self.manager.get_board_by_id(self.board_id)
        self.assertIsNotNone(board)
        self.assertEqual(board.board.actual_turn, BLACK)
        self.assertEqual(board.black_score, 0)
        self.assertEqual(board.white_score, 10)

    def test_start_game(self):
        turn_token = self.manager.challenge('user1', 'user2')
        self.assertIsNotNone(turn_token)

    def test_move_with_turn_token(self):
        board_id = self.manager.challenge('user1', 'user2')
        first_turn_token, white_username, actual_turn_color, board = self.manager.challenge_accepted(board_id)
        # initial board turn should be WHITE
        self.assertEqual(actual_turn_color, WHITE)
        # move WHITE with token
        second_turn_token, black_username, actual_turn_color, board = self.manager.move_with_turn_token(first_turn_token, 12, 3, 11, 3)
        # second board turn should be BLACK
        self.assertEqual(actual_turn_color, BLACK)
        # invalid turn token exception
        with self.assertRaises(InvalidTurnTokenException):
            self.manager.move_with_turn_token(first_turn_token, 12, 4, 11, 4)
        # move BLACK with token
        third_turn_token, white_username, actual_turn_color, board = self.manager.move_with_turn_token(second_turn_token, 3, 3, 4, 3)
        self.assertIsNotNone(third_turn_token)
        self.assertEqual(actual_turn_color, WHITE)

if __name__ == '__main__':
    unittest.main()
