from datetime import datetime
from collections import defaultdict
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
            tournament['boards'] = []
        scores = defaultdict(int)
        boards = self.chess_manager.get_boards(prefix=tournament_key)
        for board in boards:
            if with_boards:
                tournament['boards'].append(board)
            if board.white_score > board.black_score:
                scores[board.white_username] += 3
            elif board.white_score < board.black_score:
                scores[board.black_username] += 3
        if scores:
            max_score = max((value for value in scores.values()))
            winners = [
                username for username, score in scores.items() if score == max_score
            ]
        else:
            winners = []
        tournament['winners'] = winners
        tournament['scores'] = scores
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
        move_left = 200
        tournament_key = self.get_tournament_key(tournament_id)
        for user_white, user_black in combinations(users, 2):
            boards.append(
                self.chess_manager.create_board(
                    user_white.decode(),
                    user_black.decode(),
                    move_left,
                    prefix=tournament_key,
                ),
            )
        return boards

    def board_finish(self, board_id):
        # board_id ~ board:[tournament:<tournament_id>]::<board_id>
        # playing_board = self.chess_manager.get_board_by_id(board_id)
        tournament_key = board_id.split(':')[2]
        boards = self.chess_manager.get_boards(prefix=tournament_key)
        # for board in boards:

