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

        self.fdout = open('outdump', 'w')

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = True
        self.sock.connect((self.host, self.port))
        self.sock.send(b'\x1bbc 1\n')

    def readline(self, block = 0):
        # try to stay connected
        if not self.connected:
            raise ConnectionDead()

        if self.inbuf.find(b'\n') < 0 and self.inbuf.find(b'\xff\xf9') < 0 and self.inbuf.find(b'\x1b>'):
            # no pending line so wait if needed
            self.sock.settimeout(block)
        else:
            # dont wait, we have a pending line
            self.sock.settimeout(0)
        try:
            data = self.sock.recv(4096)
            self.fdout.write('%s\n' % data)
            self.fdout.flush()
            if not data:
                raise ConnectionDead()
            self.inbuf = self.inbuf + data
        except:
            pass

        f9mark = self.inbuf.find(b'\xff\xf9')
        eols = self.inbuf.find(b'\n')
        #spbegin = self.inbuf.find(b'\x1b<')
        spbegin = -1

        # use unrealistic values
        if f9mark == -1:
            f9mark = 0x100000
        if eols == -1:
            eols =   0x100000
        if spbegin == -1:
            spbegin =0x100000


        inbuf = self.inbuf

        # do we have a special mark beginning?
        '''
        if spbegin < eols and spbegin < f9mark:
            # wait until we have a sepcial mark ending
            spend = inbuf.find(b'\x1b>')
            if spend < 0:
                return None
            # wait until we have all the character of the code
            if spend + 1 + 3 > len(inbuf):
                return None
            line = inbuf[0:spend + 4]
            self.inbuf = inbuf[spend + 4:]
            return line
        '''
        if f9mark < eols and f9mark < spbegin:
            line = self.inbuf[0:f9mark + 2]
            self.inbuf = self.inbuf[f9mark + 2:]
            return line
        if eols < f9mark and eols < spbegin:
            line = self.inbuf[0:eols].strip()
            self.inbuf = self.inbuf[eols + 1:]
            return line
        return None

    def writeline(self, line):
        if type(line) == str:
            line = bytes(line, 'utf8')
        if not self.connected:
            raise ConnectionDead()
        self.sock.send(line + b'\r\n')
        print('client sent', line)