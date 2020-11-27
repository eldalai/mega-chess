# import gevent
# from gevent.pool import Pool
import random
import traceback
import ujson
import asyncio
from quart.ctx import copy_current_websocket_context

from users import UserManager
from manager import ChessManager, GameOverException
from tournaments import TournamentManager


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


class InvalidTokenException(ControllerExcetions):
    pass


class InvalidRegisterException(ControllerExcetions):
    pass


class TimeoutException(ControllerExcetions):
    pass


class InvalidSaveTurnException(object):
    pass


class Controller:

    def __init__(self, redis_pool, app, connected_websockets):
        self.chess_manager = ChessManager(redis_pool)
        self.user_manager = UserManager(redis_pool, app)
        self.tournament_manager = TournamentManager(redis_pool, self.chess_manager)
        self.board_subscribers = {}
        self.redis_pool = redis_pool
        self.app = app
        self.connected_websockets = connected_websockets

    async def execute_message(self, client, message):
        self.app.logger.info(
            'process_message: message: {}'.format(message)
        )
        await self.process_message(client, message)

    async def get_current_username(self, client):
        auth_token = client.args.get('authtoken')
        if not auth_token:
            raise NoTokenException()
        return await self.user_manager.get_username_by_auth_token(auth_token)

    async def process_message(self, client, message):
        method_name, data = await self.parse_message(message)
        current_username = await self.get_current_username(client)
        self.app.logger.info('process_message from {}: {} {}'.format(current_username, method_name, data))
        method = getattr(self, method_name)
        try:
            await method(current_username, client, data)
            # await self.send(client, 'response_ok', data)
        except Exception as e:
            tb = traceback.format_exc()
            self.app.logger.error('exception {} {}'.format(e, tb))

            data = {
                'exception': str(type(e))
            }
            # gevent.spawn(
            await self.send(client, 'response_error', data)
            raise e

    async def parse_message(self, message):
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

    async def action_register(self, current_username, client, data):
        if not self.valid_auth(data):
            raise InvalidRegisterException()
        return self.user_manager.register(data['username'], data['password'])

    async def action_get_connected_users(self, current_username, client, data):
        self.app.logger.info('action_get_connected {} {}'.format(client, current_username))
        data = {
            'users_list': await self.get_active_users()
        }
        await self.send(client, 'update_user_list', data)

    async def action_login(self, current_username, client, data=None):
        self.app.logger.info('action_login {} {}'.format(client, current_username))
        client.username = current_username
        client.queue.username = current_username
        data = {
            'users_list': await self.get_active_users()
        }
        self.app.logger.info('connected users: {}'.format(data))
        await self.broadcast('update_user_list', data)

        return True

    async def get_active_users(self):
        return {
            queue.username for queue in self.connected_websockets
            if hasattr(queue, 'username')
        }

    def get_username_by_client(self, client):
        for queue in self.connected_websockets:
            if(
                hasattr(queue, 'webservice') and
                queue.webservice == client and
                hasattr(queue, 'username')
            ):
                return queue.username

    async def action_challenge(self, current_username, client, data):
        challenged_username = data['username']
        challenger_username = current_username
        await self._challenge(challenger_username, challenged_username)

    async def challenge_with_auth_token(self, auth_token, username, message):
        challenger_username = await self.user_manager.get_username_by_auth_token(auth_token)
        return await self._challenge(challenger_username, username)

    async def _challenge(self, challenger_username, challenged_username):
        self.app.logger.info('action_challenge {} from {}'.format(challenged_username, challenger_username))
        if random.choice([True, False]):
            white_username = challenger_username
            black_username = challenged_username
        else:
            white_username = challenged_username
            black_username = challenger_username
        move_left = 200
        board_id = self.chess_manager.challenge(
            white_username=white_username,
            black_username=black_username,
            move_left=move_left,
        )
        data = {
            'username': challenger_username,
            'board_id': board_id,
        }
        await self.broadcast('ask_challenge', data, challenged_username)
        return True

    async def broadcast(self, event, data, username=None):
        for queue in self.connected_websockets:
            if(
                not username or
                (
                    hasattr(queue, 'username') and
                    username == queue.username
                )
            ):
                message = {
                    'event': event,
                    'data': data,
                }
                await queue.put(ujson.dumps(message))

    async def action_accept_challenge(self, current_username, client, data):
        board_id = data['board_id']
        await self._start_board(board_id)
        return True

    async def _start_board(self, board_id):
        turn_token, username, actual_turn, board, move_left, opponent_username = self.chess_manager.challenge_accepted(board_id)
        next_turn_data = {
            'board_id': board_id,
            'turn_token': turn_token,
            'username': username,
            'actual_turn': actual_turn,
            'board': board,
            'move_left': move_left,
            'opponent_username': opponent_username,
        }
        self.app.logger.info('action_accept_challenge ok'.format(board_id, next_turn_data))
        await self.set_next_turn(board_id, next_turn_data)

    async def action_abort(self, current_username, client, data):
        board_id = data['board_id']
        self.chess_manager.abort(board_id, current_username)
        await self.send_gameover(board_id)

    async def action_move(self, current_username, client, data):
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
            turn_token, username, actual_turn, board, move_left, opponent_username = self.chess_manager.move_with_turn_token(
                turn_token=data['turn_token'],
                from_row=data['from_row'],
                from_col=data['from_col'],
                to_row=data['to_row'],
                to_col=data['to_col'],
            )
            processed = True
        except GameOverException:
            await self.send_gameover(board_id)
            return
        except Exception as e:
            tb = traceback.format_exc()
            try:
                self.app.logger.error('action_move {} exception  {} {}'.format(board_id, e, tb))
                await self.force_change_turn(data['board_id'], data['turn_token'])
                return
                # turn_token, username, actual_turn, board, move_left = self.chess_manager._next_turn_token(board_id)
            except GameOverException:
                await self.send_gameover(board_id)
                return
        next_turn_data = {
            'board_id': board_id,
            'turn_token': turn_token,
            'username': username,
            'actual_turn': actual_turn,
            'board': board,
            'move_left': move_left,
            'opponent_username': opponent_username,
        }
        await self.set_next_turn(board_id, next_turn_data)

    def get_next_turn_key(self, board_id, turn_token):
        return "next_turn:{}:{}".format(board_id, turn_token)

    async def set_next_turn(self, board_id, next_turn_data):
        self.app.logger.info('set_next_turn {} {}'.format(board_id, next_turn_data))
        key = self.get_next_turn_key(board_id, next_turn_data['turn_token'])
        self.redis_pool.set(key, ujson.dumps(next_turn_data))
        await self.enqueue_next_turn(key)
        # if not self._save_turn(next_turn_data):
        #     raise InvalidSaveTurnException()

    async def enqueue_next_turn(self, key):
        self.app.logger.info('enqueue_next_turn {}'.format(key))
        # self.redis_pool.rpush("next_turn_queue", key)
        # self.pool.wait_available()
        # self.pool.spawn(self.process_next_turn, key)
        await self.process_next_turn(key)

    def _save_turn(self, data):
        try:
            data_json = ujson.dumps(data)
            self.redis_pool.set(
                "{0}:{1}".format('turn', data['turn_token']),
                data_json)
            return True
        except Exception:
            return False

    async def send_gameover(self, board_id):
        board = self.chess_manager.get_board_by_id(board_id)
        if self.tournament_manager.get_tournament_key('') in board_id:
            self.tournament_manager.board_finish(board_id)
        data = {
            'board': board.board.get_simple(),
            'white_username': str(board.white_username),
            'black_username': str(board.black_username),
            'white_score': str(board.white_score),
            'black_score': str(board.black_score),
            'board_id': board_id,
        }
        await self.broadcast('gameover', data, board.white_username)
        await self.broadcast('gameover', data, board.black_username)

    async def force_change_turn(self, board_id, turn_token):
        self.app.logger.info('force_change_turn {} {}'.format(board_id, turn_token))
        try:
            turn_token, username, actual_turn, board, move_left, opponent_username = self.chess_manager.force_change_turn(board_id, turn_token)
        except GameOverException:
            await self.send_gameover(board_id)
            return
        next_turn_data = {
                'board_id': board_id,
                'turn_token': turn_token,
                'username': username,
                'actual_turn': actual_turn,
                'board': board,
                'move_left': move_left,
                'opponent_username': opponent_username,
        }
        self.app.logger.info('force_change_turn set_next_turn {} {}'.format(board_id, turn_token))
        await self.set_next_turn(board_id, next_turn_data)

    async def process_next_turn(self, key):
        self.app.logger.info('process_next_turn {}'.format(key))
        try:
            # key = self.redis_pool.blpop('next_turn_queue')
            if not key:
                self.app.logger.info('Nothing pending to process')
                return
            data = ujson.loads(self.redis_pool.get(key))
            self.app.logger.info('next_turn key: {} data: {}'.format(key, data))
            await self.broadcast('your_turn', data, data['username'])
            # self.notify_to_board_subscribers(data['board_id'])
            # control timeout
            await asyncio.sleep(30)
            self.app.logger.info('Checking timeout {} {}'.format(data['board_id'], data['turn_token']))
            if self.redis_pool.exists(key):
                self.app.logger.info('Forcing timeout {} {}'.format(data['board_id'], data['turn_token']))
                self.redis_pool.delete(key)
                await self.force_change_turn(data['board_id'], data['turn_token'])
        except Exception as e:
            tb = traceback.format_exc()
            self.app.logger.error('process_next_turn {} exception  {} {}'.format(key, e, tb))
        self.app.logger.info('end process_next_turn {}'.format(key))

    def notify_to_board_subscribers(self, board_id):
        board = self.chess_manager.get_board_by_id(board_id)
        for board_subscriber_client in self.board_subscribers.get(board_id, []):
            self.notify_board_update(board_subscriber_client, board)

    async def notify_board_update(self, board_subscriber_client, board):
        data = {
            'board': board.board.get_simple(),
            'white_username': board.white_username,
            'black_username': board.black_username,
            'white_score': board.white_score,
            'black_score': board.black_score,

        }
        await self.send(board_subscriber_client, 'update_board', data)

    async def action_subscribe(self, current_username, client, data):
        board_id = data['board_id']
        board = self.chess_manager.get_board_by_id(board_id)
        if board_id not in self.board_subscribers:
            self.board_subscribers[board_id] = []
        self.board_subscribers[board_id].append(client)
        self.notify_board_update(client, board)
        return True

    async def send(self, client, event, data):
        """
        Send given data to the registered client.
        Automatically discards invalid connections.
        """
        try:
            self.app.logger.info(u'send to client: {}, event: {}, data: {}'.format(client, event, data))
            message = {
                'event': event,
                'data': data,
            }
            # print 'sent to {0}: {1}'.format(client, message)
            await client.send(ujson.dumps(message))
        except Exception:
            pass
            #  app.logger.info(u'Exception on sending to client: {}'.format(client))
            #  self.clients.remove(client)

    async def action_create_tournament(self, current_username, client, data):
        tournament = self.tournament_manager.create_tournament()
        await self.send(client, 'tournament_created', tournament)
        return True

    async def action_add_user_to_tournament(self, current_username, client, data):
        tournament_id = data['tournament_id']
        username = data['username']
        self.tournament_manager.add_user(tournament_id, username)
        users = self.tournament_manager.get_users(tournament_id)
        await self.send(client, 'user_added_to_tournament', users)
        return True

    async def action_start_tournament(self, current_username, client, data):
        tournament_id = data['tournament_id']
        tournament = self.tournament_manager.get_tournament(tournament_id)
        # TODO: control and change state...
        boards = self.tournament_manager.start(tournament_id)
        for board_id in boards:
            asyncio.create_task(self._start_board(board_id))
        users = self.tournament_manager.get_users(tournament_id)

        await self.send(client, 'tournament_started', users)
        return True
