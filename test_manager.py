import unittest
import ujson

import fakeredis
from freezegun import freeze_time

from pychess.chess import (
    BLACK,
    WHITE,
    InvalidTurnException,
)

from manager import (
    ChessManager,
    BoardFactory,
    InvalidBoardIdException,
    InvalidTurnTokenException,
    PlayingBoard,
)


class TestChessManager(unittest.TestCase):

    def setUp(self):
        super(TestChessManager, self).setUp()
        self.fake_redis = fakeredis.FakeStrictRedis()
        self.manager = ChessManager(self.fake_redis)
        self.board_id = self.manager.create_board(
            white_username='white',
            black_username='black',
            move_left=10,
        )

    def test_get_invalid_board(self):
        with self.assertRaises(InvalidBoardIdException):
            self.manager.get_board_by_id('hola-mundo')

    def test_save(self):
        _board = BoardFactory.size_16()
        board_id = '1234567890'
        with freeze_time('2020-10-20 13:15:32'):
            board = PlayingBoard(_board, 'white player', 'black player', 10)
        self.manager._save_board(board_id, board)
        self.assertTrue(self.fake_redis.exists('board:1234567890'))
        saved_boar_str = self.fake_redis.get('board:1234567890')
        restored_board = ujson.loads(saved_boar_str)
        board_str = (
            ('rrhhbbqqkkbbhhrr' * 2) +
            ('pppppppppppppppp' * 2) +
            ('                ' * 8) +
            ('PPPPPPPPPPPPPPPP' * 2) +
            ('RRHHBBQQKKBBHHRR' * 2)
        )
        expected_board = {
            'board': {
                'actual_turn': 'white',
                'size': 16,
                'board': board_str
            },
            'white_username': 'white player',
            'black_username': 'black player',
            'turn_token': None,
            'board_id': None,
            'white_score': 0,
            'black_score': 0,
            'move_left': 10,
            'created': '2020-10-20 13:15:32',
        }
        self.assertEqual(
            restored_board,
            expected_board,
        )

    def test_create_board(self):
        board = self.manager.get_board_by_id(self.board_id)
        self.assertIsNotNone(board)
        self.assertEqual(board.board.actual_turn, WHITE)
        self.assertEqual(board.white_score, 0)
        self.assertEqual(board.black_score, 0)
        self.assertTrue(self.fake_redis.exists('board:{}'.format(self.board_id)))

    def test_invalid_move(self):
        with self.assertRaises(InvalidTurnException):
            self.manager.move(self.board_id, 2, 3, 3, 3)
        board = self.manager.get_board_by_id(self.board_id)
        self.assertIsNotNone(board)
        self.assertEqual(board.board.actual_turn, WHITE)
        self.assertEqual(board.white_score, 0)
        self.assertEqual(board.black_score, 0)

    def test_move(self):
        self.manager.move(self.board_id, 12, 3, 11, 3)
        board = self.manager.get_board_by_id(self.board_id)
        self.assertIsNotNone(board)
        self.assertEqual(board.board.actual_turn, BLACK)
        self.assertEqual(board.black_score, 0)
        self.assertEqual(board.white_score, 10)

    def test_start_game(self):
        turn_token = self.manager.challenge('user1', 'user2', 10)
        self.assertIsNotNone(turn_token)

    def test_move_with_turn_token(self):
        board_id = self.manager.challenge('user1', 'user2', 10)
        first_turn_token, white_username, actual_turn_color, board, move_left = self.manager.challenge_accepted(board_id)
        # initial board turn should be WHITE
        self.assertEqual(actual_turn_color, WHITE)
        self.assertEqual(move_left, 9)
        # move WHITE with token
        second_turn_token, black_username, actual_turn_color, board, move_left = self.manager.move_with_turn_token(first_turn_token, 12, 3, 11, 3)
        # second board turn should be BLACK
        self.assertEqual(actual_turn_color, BLACK)
        self.assertEqual(move_left, 8)
        # invalid turn token exception
        with self.assertRaises(InvalidTurnTokenException):
            self.manager.move_with_turn_token(first_turn_token, 12, 4, 11, 4)
        # move BLACK with token
        third_turn_token, white_username, actual_turn_color, board, move_left = self.manager.move_with_turn_token(second_turn_token, 3, 3, 4, 3)
        self.assertIsNotNone(third_turn_token)
        self.assertEqual(actual_turn_color, WHITE)
        self.assertEqual(move_left, 7)

    def test_save_user_stats(self):
        board = self.manager.get_board_by_id(self.board_id)
        self.manager._save_user_stats(board)
        self.assertTrue(
            self.fake_redis.exists(self.manager.get_user_stats_key('white'))
        )
        self.assertTrue(
            self.fake_redis.exists(self.manager.get_user_stats_key('black'))
        )
        self.assertEqual(
            self.fake_redis.llen(self.manager.get_user_stats_key('white')),
            1,
        )
        self.assertEqual(
            self.fake_redis.llen(self.manager.get_user_stats_key('black')),
            1,
        )


if __name__ == '__main__':
    unittest.main()
