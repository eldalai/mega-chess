import bcrypt
import ujson
import redis


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

    def register(self, username, password):
        if self.redis_pool.exists(self._user_id(username)):
            raise UserAlreadyExistsException()
        hash_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())
        user = ujson.dumps({
            'username': username,
            'password': hash_password,
            'clients': [],
        })
        self.redis_pool.set(self._user_id(username), user)
        return True

    def login(self, username, password, client):
        if not self.redis_pool.exists(self._user_id(username)):
            raise InvalidAuthLoginException()
        user_string = self.redis_pool.get(self._user_id(username))
        user = ujson.loads(user_string)
        if username not in user['username']:
            raise InvalidAuthLoginException()
        if bcrypt.checkpw(password.encode('utf-8'),
                          user['password'].encode('utf-8')) is False:
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
