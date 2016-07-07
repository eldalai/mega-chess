
class UserException(Exception):
    pass


class UserAlreadyExistsException(UserException):
    pass


class InvalidAuthLoginException(UserException):
    pass


class UserManager(object):

    def __init__(self):
        super(UserManager, self).__init__()
        self.users = {}

    def register(self, username, password):
        if username in self.users:
            raise UserAlreadyExistsException()
        self.users[username] = {
            'username': username,
            'password': password,
            'clients': [],
        }
        return True

    def login(self, username, password, client):
        if username not in self.users:
            raise InvalidAuthLoginException()
        if self.users[username]['password'] != password:
            raise InvalidAuthLoginException()
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
