import unittest

import fakeredis

from manager import ChessManager
from tournaments import TournamentManager, InvalidTournamentIdException


class TestTournament(unittest.TestCase):

    def setUp(self):
        super(TestTournament, self).setUp()
        self.redis_pool = fakeredis.FakeStrictRedis()
        self.chess_manager = ChessManager()
        self.tournament_manager = TournamentManager(
            self.redis_pool,
            self.chess_manager,
        )

    def test_create_tournament(self):
        tournament = self.tournament_manager.create_tournament()
        self.assertIsNotNone(tournament)
        self.assertIn('id', tournament)
        self.assertIn('created', tournament)

    def test_get_tournament(self):
        tournament = self.tournament_manager.create_tournament()
        tournament_get = self.tournament_manager.get_tournament(tournament['id'])
        self.assertEqual(tournament_get['created'], tournament['created'])

    def test_get_invalid_tournament(self):
        with self.assertRaises(InvalidTournamentIdException):
            self.tournament_manager.get_tournament('invalid_id')

    def test_add_user_to_tournament(self):
        tournament = self.tournament_manager.create_tournament()
        self.tournament_manager.add_user(tournament['id'], 'random')
        users_in_tournament = self.tournament_manager.get_users(tournament['id'])
        self.assertEqual(users_in_tournament, {b'random'})
        self.tournament_manager.add_user(tournament['id'], 'admin')
        users_in_tournament = self.tournament_manager.get_users(tournament['id'])
        self.assertEqual(users_in_tournament, {b'random', b'admin'})

    def test_start_simple_tournament(self):
        tournament = self.tournament_manager.create_tournament()
        self.tournament_manager.add_user(tournament['id'], 'random')
        self.tournament_manager.add_user(tournament['id'], 'admin')
        self.tournament_manager.start(tournament['id'])
        self.assertEqual(len(self.chess_manager.boards.keys()), 1)

    def test_start_3_players_tournament(self):
        tournament = self.tournament_manager.create_tournament()
        self.tournament_manager.add_user(tournament['id'], 'random')
        self.tournament_manager.add_user(tournament['id'], 'admin')
        self.tournament_manager.add_user(tournament['id'], 'dummy')
        self.tournament_manager.start(tournament['id'])
        self.assertEqual(len(self.chess_manager.boards.keys()), 3)

    def test_start_3_players_tournament(self):
        tournament = self.tournament_manager.create_tournament()
        self.tournament_manager.add_user(tournament['id'], 'random')
        self.tournament_manager.add_user(tournament['id'], 'admin')
        self.tournament_manager.add_user(tournament['id'], 'dummy')
        self.tournament_manager.add_user(tournament['id'], 'other')
        self.tournament_manager.start(tournament['id'])
        self.assertEqual(len(self.chess_manager.boards.keys()), 6)



if __name__ == '__main__':
    unittest.main()
