import unittest
from pychess.chess import (
    BLACK,
    WHITE,
    InvalidTurnException,
)

from manager import (
    InvalidBoardIdException,
    InvalidTurnTokenException,
    Manager,
)


class TestManager(unittest.TestCase):

    def setUp(self):
        super(TestManager, self).setUp()
        self.manager = Manager()
        self.board_id = self.manager.create_board()

    def test_get_invalid_board(self):
        with self.assertRaises(InvalidBoardIdException):
            self.manager.get_board_by_id('hola-mundo')

    def test_create_board(self):
        board = self.manager.get_board_by_id(self.board_id)
        self.assertIsNotNone(board)
        self.assertEqual(board.actual_turn, WHITE)

    def test_invalid_move(self):
        with self.assertRaises(InvalidTurnException):
            self.manager.move(self.board_id, 1, 3, 2, 3)
        board = self.manager.get_board_by_id(self.board_id)
        self.assertIsNotNone(board)
        self.assertEqual(board.actual_turn, WHITE)

    def test_move(self):
        self.manager.move(self.board_id, 6, 3, 5, 3)
        board = self.manager.get_board_by_id(self.board_id)
        self.assertIsNotNone(board)
        self.assertEqual(board.actual_turn, BLACK)

    def test_start_game(self):
        turn_token = self.manager.challenge('user1', 'user2')
        self.assertIsNotNone(turn_token)

    def test_move_with_turn_token(self):
        first_turn_token = self.manager.challenge('user1', 'user2')
        # initial board turn should be WHITE
        board_id = self.manager.get_board_id_by_turn_token(first_turn_token)
        board = self.manager.get_board_by_id(board_id)
        self.assertEqual(board.actual_turn, WHITE)
        # move WHITE with token
        second_turn_token = self.manager.move_with_turn_token(first_turn_token, 6, 3, 5, 3)
        # second board turn should be BLACK
        board_id = self.manager.get_board_id_by_turn_token(second_turn_token)
        board = self.manager.get_board_by_id(board_id)
        self.assertEqual(board.actual_turn, BLACK)
        # invalid turn token exception
        with self.assertRaises(InvalidTurnTokenException):
            self.manager.move_with_turn_token(first_turn_token, 6, 3, 5, 3)
        # move BLACK with token
        third_turn_token = self.manager.move_with_turn_token(second_turn_token, 1, 3, 2, 3)
        self.assertIsNotNone(third_turn_token)
        board_id = self.manager.get_board_id_by_turn_token(third_turn_token)
        board = self.manager.get_board_by_id(board_id)
        self.assertEqual(board.actual_turn, WHITE)

if __name__ == '__main__':
    unittest.main()
