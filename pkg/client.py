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

        if self.inbuf.find(b'\n') < 0 and self.inbuf.find(b'\xff\xf9') < 0:
            # no pending line so wait if needed
            self.sock.settimeout(block)
        else:
            # dont wait, we have a pending line
            self.sock.settimeout(0)
        try:
            data = self.sock.recv(4096)
            if not data:
                raise ConnectionDead()
            print('data', data)
            self.inbuf = self.inbuf + data
        except:
            pass

        f9mark = self.inbuf.find(b'\xff\xf9')
        # try to get line
        eols = self.inbuf.find(b'\n')

        if f9mark > -1 and (eols < 0 or f9mark < eols):
            line = self.inbuf[0:f9mark + 2]
            self.inbuf = self.inbuf[f9mark + 2:]
            print('f9markline', line)
            return line
        if eols > -1 and (f9mark < 0 or eols < f9mark):
            line = self.inbuf[0:eols].strip()
            self.inbuf = self.inbuf[eols + 1:]
            print('eolsline', line)
            return line
        return None

    def writeline(self, line):
        if type(line) == str:
            line = bytes(line, 'utf8')
        if not self.connected:
            raise ConnectionDead()
        self.sock.send(line + b'\r\n')
        print('client sent', line)