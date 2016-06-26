import unittest
from pychess.chess import (
    BLACK,
    WHITE,
    InvalidTurnException,
)

from manager import (
    InvalidBoardIdException,
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

if __name__ == '__main__':
    unittest.main()
