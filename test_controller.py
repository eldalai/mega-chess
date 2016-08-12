import json
from mock import (
    MagicMock,
    Mock,
    patch,
    PropertyMock,
)
import unittest
from controller import (
    Controller,
    InvalidActionNameException,
    InvalidActionFormatException,
    InvalidNoActionException,
    InvalidNoDataException,
    InvalidLoginException,
    InvalidRegisterException,
)
from users import (
    InvalidAuthLoginException,
    UserAlreadyExistsException,
)


class TestActionsSwitcher(unittest.TestCase):

    def setUp(self):
        super(TestActionsSwitcher, self).setUp()
        self.controller = Controller()
        self.mock_client = MagicMock()
        self.mock_client_2 = MagicMock()
        closed_property = PropertyMock(return_value=False)
        type(self.mock_client).closed = closed_property
        type(self.mock_client_2).closed = closed_property
        self.mock_client.send = Mock()
        self.mock_client_2.send = Mock()

    def test_wrong_action(self):
        with self.assertRaises(InvalidActionFormatException):
            self.controller.execute_message(
                client=self.mock_client,
                message='Hola Mundo',
            )

    def test_no_action_provided(self):
        with self.assertRaises(InvalidNoActionException):
            self.controller.execute_message(
                client=self.mock_client,
                message='{"hola": "mundo"}',
            )

    def test_invalid_action(self):
        with self.assertRaises(InvalidActionNameException):
            self.controller.execute_message(
                client=self.mock_client,
                message='{"action": "hola"}'
            )

    def test_invalid_data(self):
        with self.assertRaises(InvalidNoDataException):
            self.controller.execute_message(
                client=self.mock_client,
                message='{"action": "login"}'
            )

    def test_invalid_register_action(self):
        with self.assertRaises(InvalidRegisterException):
            self.controller.execute_message(
                client=self.mock_client,
                message='{"action": "register", "data": {"blah": "gabriel"} }'
            )
        with self.assertRaises(InvalidRegisterException):
            self.controller.execute_message(
                client=self.mock_client,
                message='{"action": "register", "data": {"username": "gabriel"} }'
            )

    def test_valid_register_action(self):
        result = self.controller.execute_message(
            client=self.mock_client,
            message='{"action": "register", "data": {"username": "test_valid_register_action", "password": "12345678"} }'
        )
        self.assertTrue(result)

    def test_invalid_register_twice_action(self):
        result = self.controller.execute_message(
            client=self.mock_client,
            message='{"action": "register", "data": {"username": "test_invalid_register_twice_action", "password": "12345678"} }'
        )
        self.assertTrue(result)
        with self.assertRaises(UserAlreadyExistsException):
            self.controller.execute_message(
                client=self.mock_client,
                message='{"action": "register", "data": {"username": "test_invalid_register_twice_action", "password": "12345678"} }'
            )

    def test_invalid_login_action(self):
        with self.assertRaises(InvalidLoginException):
            self.controller.execute_message(
                client=self.mock_client,
                message='{"action": "login", "data": {"blah": "gabriel"} }'
            )
        with self.assertRaises(InvalidLoginException):
            self.controller.execute_message(
                client=self.mock_client,
                message='{"action": "login", "data": {"username": "test_invalid_login_action"} }'
            )

    def test_unregister_login_action(self):
        with self.assertRaises(InvalidAuthLoginException):
            self.controller.execute_message(
                client=self.mock_client,
                message='{"action": "login", "data": {"username": "test_unregister_login_action", "password": "12345678"} }'
            )

    def test_invalid_password_login_action(self):
        response = self.controller.execute_message(
            client=self.mock_client,
            message='{"action": "register", "data": {"username": "test_invalid_password_login_action", "password": "12345678"} }'
        )
        self.assertTrue(response)
        with self.assertRaises(InvalidAuthLoginException):
            self.controller.execute_message(
                client=self.mock_client,
                message='{"action": "login", "data": {"username": "test_invalid_password_login_action", "password": "WRONG!"} }'
            )

    def test_valid_login_action(self):
        response = self.controller.execute_message(
            client=self.mock_client,
            message='{"action": "register", "data": {"username": "test_valid_login_action", "password": "12345678"} }'
        )
        self.assertTrue(response)
        self.mock_client.send.reset_mock()
        response = self.controller.execute_message(
            client=self.mock_client,
            message='{"action": "login", "data": {"username": "test_valid_login_action", "password": "12345678"} }'
        )
        self.assertTrue(response)
        self.assertEqual(self.mock_client.send.call_count, 2)

    def test_challenge_action(self):
        response = self.controller.execute_message(
            client=self.mock_client,
            message='{"action": "register", "data": {"username": "client1", "password": "12345678"} }'
        )
        self.assertTrue(response)
        response = self.controller.execute_message(
            client=self.mock_client_2,
            message='{"action": "register", "data": {"username": "client2", "password": "12345678"} }'
        )
        self.assertTrue(response)
        response = self.controller.execute_message(
            client=self.mock_client,
            message='{"action": "login", "data": {"username": "client1", "password": "12345678"} }'
        )
        response = self.controller.execute_message(
            client=self.mock_client_2,
            message='{"action": "login", "data": {"username": "client2", "password": "12345678"} }'
        )
        self.assertTrue(response)
        #  force random to select client1 as white player
        with patch('controller.random') as mock_random:
            mock_random.choise.return_value = True
            response = self.controller.execute_message(
                client=self.mock_client,
                message='{"action": "challenge", "data": {"username": "client2"} }'
            )
        self.assertTrue(response)

        self.mock_client.send.reset_mock()

        for call in self.mock_client_2.send.call_args_list:
            action = json.loads(call[0][0])
            if action['action'] == 'ask_challenge':
                response = self.controller.execute_message(
                    client=self.mock_client_2,
                    message='{"action": "accept_challenge", "data": {"board_id": "%(board_id)s"} }' % {'board_id': action['data']['board_id']}
                )

        self.mock_client_2.send.reset_mock()

        for call in self.mock_client.send.call_args_list:
            action = json.loads(call[0][0])
            if action['action'] == 'your_turn':
                response = self.controller.execute_message(
                    client=self.mock_client,
                    message=json.dumps({
                        "action": "move",
                        "data": {
                            "board_id": action['data']['board_id'],
                            "turn_token": action['data']['turn_token'],
                            'from_row': 6,
                            'from_col': 3,
                            'to_row': 5,
                            'to_col': 3,
                        }
                    })
                )

        for call in self.mock_client_2.send.call_args_list:
            action = json.loads(call[0][0])
            if action['action'] == 'your_turn':
                response = self.controller.execute_message(
                    client=self.mock_client_2,
                    message=json.dumps({
                        "action": "move",
                        "data": {
                            "board_id": action['data']['board_id'],
                            "turn_token": action['data']['turn_token'],
                            'from_row': 1,
                            'from_col': 3,
                            'to_row': 2,
                            'to_col': 3,
                        }
                    })
                )

        response = self.controller.execute_message(
            client=self.mock_client_2,
            message=json.dumps({
                "action": "subscribe",
                "data": {
                    "board_id": action['data']['board_id'],
                }
            })
        )


if __name__ == '__main__':
    unittest.main()
