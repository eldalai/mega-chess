from datetime import datetime
import ujson
import uuid


class InvalidTournamentIdException(Exception):
    pass


PENDING = 'pending'
BROKEN = 'broken'
PLAYING = 'broken'
FINISH = 'finish'


class TournamentManager():
    def __init__(self, redis_pool, chess_manager):
        self.redis_pool = redis_pool
        self.chess_manager = chess_manager

    def get_tournament(self, tournament_id, with_boards=False):
        tournament_key = self.get_tournament_key(tournament_id)
        if not self.redis_pool.exists(tournament_key):
            raise InvalidTournamentIdException()
        tournament = self.get_tournament_by_key(tournament_key)
        tournament['users'] = self.get_users(tournament_id)
        if with_boards:
            tournament['boards'] = self.chess_manager.get_boards(prefix=tournament_id)
        return tournament

    def get_tournament_by_key(self, tournament_key):
        try:
            tournament_str = self.redis_pool.get(tournament_key)
            return ujson.loads(tournament_str)
        except Exception:
            return {'id': tournament_key, 'status': BROKEN}

    def get_tournaments(self):
        all_tournaments = self.get_tournament_key('*')
        all_tournaments_keys = self.redis_pool.keys(all_tournaments)
        return [
            self.get_tournament_by_key(tournament_key)
            for tournament_key in all_tournaments_keys
        ]

    def get_tournament_key(self, tournament_id):
        return "tournament:{}".format(tournament_id)

    def get_users_tournament_key(self, tournament_id):
        return "tournament-users:{}".format(tournament_id)

    def create_tournament(self):
        tournament_id = str(uuid.uuid4())
        tournament = {
            'id': tournament_id,
            'created': datetime.now().strftime('%m-%d-%Y, %H:%M:%S'),
            'status': PENDING,
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
        users = tournament['users']
        from itertools import combinations
        boards = []
        move_left = 50
        for user_white, user_black in combinations(users, 2):
            boards.append(
                self.chess_manager.create_board(
                    user_white.decode(),
                    user_black.decode(),
                    move_left,
                    prefix=tournament_id,
                ),
            )
        return boards
