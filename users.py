import bcrypt
import ujson


class UserException(Exception):
    pass


class UserAlreadyExistsException(UserException):
    pass


class InvalidAuthLoginException(UserException):
    pass


class UserManager(object):

    def __init__(self, redis_pool):
        super(UserManager, self).__init__()
        self.redis_pool = redis_pool
        self.users = {}

    def _user_id(self, username):
        return 'user:{}'.format(username)

    def _save_user(self, username, password):
        try:
            hash_password = bcrypt.hashpw(
                password.encode('utf-8'), bcrypt.gensalt())
            user = ujson.dumps({
                'username': username,
                'password': hash_password,
                'clients': [],
            })
            self.redis_pool.set(self._user_id(username), user)
        except Exception as e:
            raise e

    def _is_password_valid(self, password, user):
        return bcrypt.checkpw(password.encode('utf-8'),
                              user['password'].encode('utf-8'))

    def register(self, username, password):
        if self.redis_pool.exists(self._user_id(username)):
            raise UserAlreadyExistsException()
        self._save_user(username, password)
        return True

    def login(self, username, password, client):
        user = self.get_user_by_username(username)
        if self._is_password_valid(password, user) is False:
            raise InvalidAuthLoginException()
        self.users[username] = user
        self.users[username]['clients'].append(client)
        return True

    @property
    def active_user_list(self):
        actives = []
        for username, user in self.users.items():
            for client in user['clients']:
                if not client.closed:
                    actives.append(username)
                    break
        return actives

    @property
    def active_clients(self):
        actives = []
        for user in self.users.values():
            for client in user['clients']:
                if not client.closed:
                    actives.append(client)
        return actives

    def get_user_by_username(self, username):
        if not self.redis_pool.exists(self._user_id(username)):
            raise InvalidAuthLoginException()
        user_string = self.redis_pool.get(self._user_id(username))
        user = ujson.loads(user_string)
        if username not in user['username']:
            raise InvalidAuthLoginException()
        return user

    def get_username_by_client(self, client):
        for user in self.users.values():
            for active_client in user['clients']:
                if active_client == client:
                    return user['username']

    def get_clients_by_username(self, username):
        if username in self.users:
            return self.users[username]['clients']
        else:
            return []
