import gevent
import json
import random

from users import UserManager
from manager import ChessManager


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


class Controller(object):

    chess_manager = ChessManager()
    user_manager = UserManager()

    def execute_message(self, client, message):
        try:
            print 'sent from {0}: {1}'.format(client, message)
            method_name, data = self.parse_message(message)
            result = self.process_message(client, method_name, data)
            # gevent.spawn(
            controller.send(client, 'response_ok', data)
            return result
        except Exception, e:
            #  TODO: change exception...
            data = {
                'exception': str(type(e))
            }
            # gevent.spawn(
            controller.send(client, 'response_error', data)
            raise e

    def process_message(self, client, method_name, data):
        method = getattr(controller, method_name)
        # Call the method as we return it
        return method(client, data)

    def parse_message(self, message):
        try:
            job = json.loads(message)
        except ValueError:
            raise InvalidActionFormatException()

        if 'action' not in job:
            raise InvalidNoActionException()
        action_name = job['action']
        method_name = 'action_' + str(action_name)
        if not hasattr(controller, method_name):
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
        if not self.valid_auth(data):
            raise InvalidLoginException()
        if self.user_manager.login(data['username'], data['password'], client):
            data = {
                'users_list': self.user_manager.active_user_list
            }
            for active_clients in self.user_manager.active_clients:
                # gevent.spawn(
                self.send(client, 'update_user_list', data)
        return True

    def action_accept_challenge(self, client, data):
        board_id = data['board_id']
        (turn_token, username) = self.chess_manager.challenge_accepted(board_id)
        data = {
            'turn_token': turn_token,
            'board_id': board_id,
        }
        for challenged_client in self.user_manager.get_clients_by_username(username):
            self.send(challenged_client, 'your_turn', data)
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

    def action_move(self, client, data):
        board_id = data['board_id']
        (turn_token, username) = self.chess_manager.move_with_turn_token(
            turn_token=data['turn_token'],
            from_row=data['from_row'],
            from_col=data['from_col'],
            to_row=data['to_row'],
            to_col=data['to_col'],
        )
        data = {
            'turn_token': turn_token,
            'board_id': board_id,
        }
        for next_client in self.user_manager.get_clients_by_username(username):
            self.send(next_client, 'your_turn', data)
        return True

    def send(self, client, action, data):
        """
        Send given data to the registered client.
        Automatically discards invalid connections.
        """
        try:
            #  app.logger.info(u'send to client: {}'.format(client))
            message = {
                'action': action,
                'data': data,
            }
            print 'sent to {0}: {1}'.format(client, message)
            client.send(json.dumps(message))
        except Exception:
            pass
            #  app.logger.info(u'Exception on sending to client: {}'.format(client))
            #  self.clients.remove(client)

controller = Controller()
