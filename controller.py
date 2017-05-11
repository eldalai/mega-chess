import gevent
from gevent.pool import Pool
import random
import traceback
import ujson

from users import UserManager
from manager import (
    ChessManager,
    GameOverException,
)


class ControllerExcetions(Exception):
    pass


class InvalidActionFormatException(ControllerExcetions):
    pass


class InvalidNoActionException(ControllerExcetions):
    pass


class InvalidActionNameException(ControllerExcetions):
    pass


class InvalidNoDataException(ControllerExcetions):
    pass


class InvalidLoginException(ControllerExcetions):
    pass


class InvalidRegisterException(ControllerExcetions):
    pass


class TimeoutException(ControllerExcetions):
    pass


class InvalidSaveTurnException(object):
    pass


class Controller(object):

    def __init__(self, redis_pool, app):
        self.chess_manager = ChessManager(redis_pool)
        self.user_manager = UserManager(redis_pool, app)
        self.board_subscribers = {}
        self.redis_pool = redis_pool
        self.app = app
        # self.notify_next_turn()
        self.pool = Pool(1000)
        # self.pool.start()

    def execute_message(self, client, message):
        try:
            #  print 'sent from {0}: {1}'.format(client, message)
            self.app.logger.info('ok1')
            method_name, data = self.parse_message(message)
            self.app.logger.info('ok2')
            result = self.process_message(client, method_name, data)
            self.app.logger.info('process_message: result: {}'.format(result))
            # gevent.spawn(
            self.send(client, 'response_ok', data)
            return result
        except Exception, e:
            #  TODO: change exception...
            tb = traceback.format_exc()
            self.app.logger.error('exception {} {}'.format(e, tb))

            data = {
                'exception': str(type(e))
            }
            # gevent.spawn(
            self.send(client, 'response_error', data)
            raise e

    def process_message(self, client, method_name, data):
        self.app.logger.info('process_message: {} {}'.format(method_name, data))
        method = getattr(self, method_name)
        # Call the method as we return it
        return method(client, data)

    def parse_message(self, message):
        try:
            job = ujson.loads(message)
        except ValueError:
            raise InvalidActionFormatException()

        if 'action' not in job:
            raise InvalidNoActionException()
        action_name = job['action']
        method_name = 'action_' + str(action_name)
        if not hasattr(self, method_name):
            raise InvalidActionNameException()

        if 'data' not in job:
            raise InvalidNoDataException()

        data = job['data']
        return method_name, data

    def valid_auth(self, data):
        return 'username' in data and 'password' in data

    def action_register(self, client, data):
        if not self.valid_auth(data):
            raise InvalidRegisterException()
        return self.user_manager.register(data['username'], data['password'])

    def action_login(self, client, data):
        self.app.logger.info('action_login')
        if not self.valid_auth(data):
            self.app.logger.info('invalid_auth')
            raise InvalidLoginException()

        if self.user_manager.login(data['username'], data['password'], client):
            self.app.logger.info('valid_auth')
            data = {
                'users_list': self.user_manager.active_user_list
            }
            for active_clients in self.user_manager.active_clients:
                # gevent.spawn(
                self.send(client, 'update_user_list', data)

        return True

    def action_challenge(self, client, data):
        challenged_username = data['username']
        challenger_username = self.user_manager.get_username_by_client(client)
        if random.choice([True, False]):
            white_username = challenger_username
            black_username = challenged_username
        else:
            white_username = challenged_username
            black_username = challenger_username
        board_id = self.chess_manager.challenge(
            white_username=white_username,
            black_username=black_username,
        )
        data = {
            'username': challenger_username,
            'board_id': board_id,
        }
        #  gevent.spawn(
        for challenged_client in self.user_manager.get_clients_by_username(challenged_username):
            self.send(challenged_client, 'ask_challenge', data)
        return True

    def action_accept_challenge(self, client, data):
        board_id = data['board_id']
        turn_token, username, actual_turn, board = self.chess_manager.challenge_accepted(board_id)
        next_turn_data = {
            'board_id': board_id,
            'turn_token': turn_token,
            'username': username,
            'actual_turn': actual_turn,
            'board': board,
        }
        self.app.logger.info('action_accept_challenge ok'.format(board_id, next_turn_data))
        self.set_next_turn(board_id, next_turn_data)
        return True

    def action_move(self, client, data):
        board_id = data['board_id']
        turn_token = data['turn_token']
        key = self.get_next_turn_key(board_id, turn_token)
        self.app.logger.info('action_move control timeout {}'.format(key))
        if self.redis_pool.exists(key):
            self.app.logger.info('action_move control timeout OK {}'.format(key))
            self.redis_pool.delete(key)
        else:
            # timeout...
            self.app.logger.info('action_move control timeout ERROR {}'.format(key))
            raise TimeoutException()
        processed = False
        try:
            turn_token, username, actual_turn, board = self.chess_manager.move_with_turn_token(
                turn_token=data['turn_token'],
                from_row=data['from_row'],
                from_col=data['from_col'],
                to_row=data['to_row'],
                to_col=data['to_col'],
            )
            next_turn_data = {
                'board_id': board_id,
                'turn_token': turn_token,
                'username': username,
                'actual_turn': actual_turn,
                'board': board,
            }
            self.app.logger.info('action_move ok'.format(board_id, next_turn_data))
            processed = True
        except GameOverException:
            self.send_game_over(board_id)
            return
        except Exception, e:
            tb = traceback.format_exc()
            self.app.logger.error('action_move {} exception  {} {}'.format(board_id, e, tb))
            try:
                turn_token, username, actual_turn, board = self.chess_manager._next_turn_token(board_id)
            except GameOverException:
                self.send_game_over(board_id)
                return
            next_turn_data = {
                'board_id': board_id,
                'turn_token': turn_token,
                'username': username,
                'actual_turn': actual_turn,
                'board': board,
            }
        self.set_next_turn(board_id, next_turn_data)

    def get_next_turn_key(self, board_id, turn_token):
        return "next_turn:{}:{}".format(board_id, turn_token)

    def set_next_turn(self, board_id, next_turn_data):
        self.app.logger.info('set_next_turn {} {}'.format(board_id, next_turn_data))
        key = self.get_next_turn_key(board_id, next_turn_data['turn_token'])
        self.redis_pool.set(key, ujson.dumps(next_turn_data))
        self.enqueue_next_turn(key)
        # if not self._save_turn(next_turn_data):
        #     raise InvalidSaveTurnException()

    def enqueue_next_turn(self, key):
        self.app.logger.info('enqueue_next_turn {}'.format(key))
        # self.redis_pool.rpush("next_turn_queue", key)
        self.pool.wait_available()
        self.pool.spawn(self.process_next_turn, key)

    def _save_turn(self, data):
        try:
            data_json = ujson.dumps(data)
            self.redis_pool.set(
                "{0}:{1}".format('turn', data['turn_token']),
                data_json)
            return True
        except Exception:
            return False

    def force_change_turn(self, board_id, turn_token):
        self.app.logger.info('force_change_turn {} {}'.format(board_id, turn_token))
        try:
            turn_token, username, actual_turn, board = self.chess_manager.force_change_turn(board_id, turn_token)
        except GameOverException:
            self.send_game_over(board_id)
            return
        next_turn_data = {
                'board_id': board_id,
                'turn_token': turn_token,
                'username': username,
                'actual_turn': actual_turn,
                'board': board,
        }
        self.app.logger.info('force_change_turn set_next_turn {} {}'.format(board_id, turn_token))
        self.set_next_turn(board_id, next_turn_data)

    def process_next_turn(self, key):
        self.app.logger.info('process_next_turn {}'.format(key))
        try:
            # key = self.redis_pool.blpop('next_turn_queue')
            if not key:
                self.app.logger.info('Nothing pending to process')
                return
            data = ujson.loads(self.redis_pool.get(key))

            self.app.logger.info('next_turn key: {} data: {}'.format(key, data))
            username = data['username']
            for next_client in self.user_manager.get_clients_by_username(username):
                self.send(next_client, 'your_turn', data)
            self.notify_to_board_subscribers(data['board_id'])
            # control timeout
            gevent.sleep(10)
            self.app.logger.info('Checking timeout {} {}'.format(data['board_id'], data['turn_token']))
            if self.redis_pool.exists(key):
                self.app.logger.info('Forcing timeout {} {}'.format(data['board_id'], data['turn_token']))
                self.redis_pool.delete(key)
                self.force_change_turn(data['board_id'], data['turn_token'])
        except Exception as e:
            tb = traceback.format_exc()
            self.app.logger.error('process_next_turn {} exception  {} {}'.format(key, e, tb))
            # retry
            # if key:
            #     self.enqueue_next_turn(key)
        self.app.logger.info('end process_next_turn {}'.format(key))

    def notify_to_board_subscribers(self, board_id):
        board = self.chess_manager.get_board_by_id(board_id)
        for board_subscriber_client in self.board_subscribers.get(board_id, []):
            self.notify_board_update(board_subscriber_client, board)

    def notify_board_update(self, board_subscriber_client, board):
        data = {
            'board': str(board.board),
            'white_username': board.white_username,
            'black_username': board.black_username,
            'white_score': board.white_score,
            'black_score': board.black_score,

        }
        self.send(board_subscriber_client, 'update_board', data)

    def action_subscribe(self, client, data):
        board_id = data['board_id']
        board = self.chess_manager.get_board_by_id(board_id)
        if board_id not in self.board_subscribers:
            self.board_subscribers[board_id] = []
        self.board_subscribers[board_id].append(client)
        self.notify_board_update(client, board)
        return True

    def send_game_over(self, board_id):
        board = self.chess_manager.get_board_by_id(board_id)
        data = {
            'board': str(board.board),
            'white_username': board.white_username,
            'black_username': board.black_username,
            'white_score': board.white_score,
            'black_score': board.black_score,
            'winner': board.winner,
        }
        for next_client in (
            self.user_manager.get_clients_by_username(board.white_username) +
            self.user_manager.get_clients_by_username(board.black_username)
        ):
            self.send(next_client, 'game_over', data)

    def send(self, client, action, data):
        """
        Send given data to the registered client.
        Automatically discards invalid connections.
        """
        try:
            self.app.logger.info(u'send to client: {}, action: {}, data: {}'.format(client, action, data))
            message = {
                'action': action,
                'data': data,
            }
            # print 'sent to {0}: {1}'.format(client, message)
            client.send(ujson.dumps(message))
        except Exception:
            pass
            #  app.logger.info(u'Exception on sending to client: {}'.format(client))
            #  self.clients.remove(client)
