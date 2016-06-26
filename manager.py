import uuid

from pychess.chess import BoardFactory


class ManagerException(Exception):
    pass


class InvalidBoardIdException(ManagerException):
    pass


class Manager(object):
    '''
    Responsable to map board_id with board_id

    TODO: Store/Retrieve boards from DB
    '''

    def __init__(self):
        super(Manager, self).__init__()
        self.boards = {}

    def create_board(self):
        board_id = str(uuid.uuid4())
        self.boards[board_id] = BoardFactory.with_pawns()
        return board_id

    def get_board_by_id(self, board_id):
        if board_id not in self.boards:
            raise InvalidBoardIdException()
        return self.boards[board_id]

    def move(self, board_id, from_row, from_col, to_row, to_col):
        return self.get_board_by_id(board_id).move(
            from_row,
            from_col,
            to_row,
            to_col,
        )
