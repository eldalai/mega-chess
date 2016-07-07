from mock import (
    MagicMock,
    Mock,
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
        closed_property = PropertyMock(return_value=False)
        type(self.mock_client).closed = closed_property
        self.mock_client.send = Mock()

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
        response = self.controller.execute_message(
            client=self.mock_client,
            message='{"action": "login", "data": {"username": "test_valid_login_action", "password": "12345678"} }'
        )
        self.assertTrue(response)


if __name__ == '__main__':
    unittest.main()
