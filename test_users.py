import unittest
from mock import (
    MagicMock,
    patch,
)

import fakeredis

from users import (
    UserManager,
    UserAlreadyExistsException,
    InvalidRegistrationToken,
)


@patch('users.emails.send_simple_message')
class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.fake_logger = MagicMock()
        self.fake_redis = fakeredis.FakeStrictRedis()
        self.user_manager = UserManager(
            self.fake_redis,
            self.fake_logger,
        )

    def test_register_success(self, send_simple_message_patch):
        fake_registration_token = 'ABCDEF'
        with patch('uuid.uuid4', return_value=fake_registration_token), \
             patch.dict('os.environ', {'DOMAIN_URL': 'http://MY_DOMAIN_URL'}):
            self.user_manager.register('gabriel@example.com', '12345678')
        self.assertEqual(send_simple_message_patch.call_count, 1)
        self.assertEqual(
            send_simple_message_patch.call_args[0],
            (
                'gabriel@example.com',
                'Welcome to Megachess!!',
                (
                    '<p>Please confirm your email account</p>'
                    '<a href="http://MY_DOMAIN_URL/confirm_registration?token=ABCDEF">CONFIRM YOUR REGISTRATION</a>'
                )
            ),
        )
        self.assertTrue(
            self.fake_redis.exists(
                self.user_manager._registration_id(fake_registration_token)
            )
        )

    def test_register_already_exists(self, send_simple_message_patch):
        fake_registration_token = 'ABCDEFH'
        self.user_manager._save_user('gabriel2@example.com', '<fake+pass>')
        with patch('uuid.uuid4', return_value=fake_registration_token), \
             self.assertRaises(UserAlreadyExistsException):
            self.user_manager.register('gabriel2@example.com', '12345678')
        self.assertEqual(send_simple_message_patch.call_count, 0)
        self.assertFalse(
            self.fake_redis.exists(
                self.user_manager._registration_id(fake_registration_token)
            )
        )

    def test_confirm_registration_success(self, send_simple_message_patch):
        fake_registration_token = 'ABCDEFGI'
        with patch('uuid.uuid4', return_value=fake_registration_token):
            self.user_manager.register('gabriel3@example.com', '12345678')
        fake_auth_token = 'wqerqwerqwer'
        with patch('uuid.uuid4', return_value=fake_auth_token):
            self.user_manager.confirm_registration(fake_registration_token)
        self.assertIsNotNone(
            self.user_manager.get_user_by_username('gabriel3@example.com')
        )
        self.assertFalse(
            self.fake_redis.exists(
                self.user_manager._registration_id(fake_registration_token)
            )
        )
        self.assertEqual(send_simple_message_patch.call_count, 2)
        self.assertEqual(
            send_simple_message_patch.call_args[0],
            (
                'gabriel3@example.com',
                'Your account in Megachess is confirmed!!!',
                (
                    '<p>This is your personal auth_token to play</p>'
                    '<p><strong>{}</strong></p>'
                ).format(fake_auth_token)
            ),
        )

    def test_confirm_registration_error(self, send_simple_message_patch):
        with self.assertRaises(InvalidRegistrationToken):
            self.user_manager.confirm_registration('<fake_registration_token>')


if __name__ == '__main__':
    unittest.main()
