import socket
from queue import Queue


class Client(socket.socket):
    def __init__(self, family=-1, type=-1, proto=-1, fileno=None):
        super().__init__(family, type, proto, fileno)

        self.recv_buff = Queue()
        self.send_buff = Queue()

        self.username = str(self.fileno())
        self.ip = ""

    def accept(self):
        fd, addr = self._accept()

        st = Client(
            self.family,
            self.type,
            self.proto,
            fileno=fd
        )

        return st, addr

    def __repr__(self):
        return repr(self.username)

    def __hash__(self):
        return hash(self.username)

    def __eq__(self, other):
        return hash(other) == hash(self)
