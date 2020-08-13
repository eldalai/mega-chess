from datetime import datetime
import ujson
import uuid


class InvalidTournamentIdException(Exception):
    pass


class TournamentManager():
    def __init__(self, redis_pool, chess_manager):
        self.redis_pool = redis_pool
        self.chess_manager = chess_manager

    def get_tournament(self, tournament_id):
        tournament_key = self.get_tournament_key(tournament_id)
        if not self.redis_pool.exists(tournament_key):
            raise InvalidTournamentIdException()
        tournament_str = self.redis_pool.get(tournament_key)
        return ujson.loads(tournament_str)

    def get_tournament_key(self, tournament_id):
        return "tournament:{}".format(tournament_id)

    def get_users_tournament_key(self, tournament_id):
        return "tournament:users:{}".format(tournament_id)

    def create_tournament(self):
        tournament_id = str(uuid.uuid4())
        tournament = {
            'id': tournament_id,
            'created': datetime.now().strftime('%m-%d-%Y, %H:%M:%S'),
        }
        self.redis_pool.set(
            self.get_tournament_key(tournament_id),
            ujson.dumps(tournament),
        )
        return tournament

    def add_user(self, tournament_id, user):
        tournament_key = self.get_tournament_key(tournament_id)
        if not self.redis_pool.exists(tournament_key):
            raise InvalidTournamentIdException()
        users_tournament_key = self.get_users_tournament_key(tournament_id)
        self.redis_pool.sadd(users_tournament_key, user)

    def get_users(self, tournament_id):
        tournament_key = self.get_tournament_key(tournament_id)
        if not self.redis_pool.exists(tournament_key):
            raise InvalidTournamentIdException()
        users_tournament_key = self.get_users_tournament_key(tournament_id)
        return self.redis_pool.smembers(users_tournament_key)

    def start(self, tournament_id):
        tournament = self.get_tournament(tournament_id)
        # TODO: change state
        users = self.get_users(tournament_id)
        from itertools import combinations
        boards = []
        for user_white, user_black in combinations(users, 2):
            boards.append(
                self.chess_manager.create_board(user_white, user_black),
            )
        return boards
