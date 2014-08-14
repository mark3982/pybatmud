import socket

class ConnectionDead(Exception):
    pass

class Client:
    def __init__(self, host, port):
        self.inbuf = b''
        self.inlines = []
        self.connected = False
        self.host = host
        self.port = port
        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = True
        self.sock.connect((self.host, self.port))

    def readline(self, block = 0):
        # try to stay connected
        if not self.connected:
            raise ConnectionDead()

        if self.inbuf.find(b'\n') < 0:
            # no pending line so wait if needed
            self.sock.settimeout(block)
        else:
            # dont wait, we have a pending line
            self.sock.settimeout(0)
        try:
            data = self.sock.recv(4096)
            if not data:
                raise ConnectionDead()
            self.inbuf = self.inbuf + data
        except:
            pass

        # try to get line
        eols = self.inbuf.find(b'\n')
        if eols < 0:
            return None
        line = self.inbuf[0:eols].strip()
        self.inbuf = self.inbuf[eols + 1:]

        return line

    def writeline(self, line):
        if type(line) == str:
            line = bytes(line, 'utf8')
        if not self.connected:
            raise ConnectionDead()
        self.sock.send(line + b'\n')