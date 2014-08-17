import socket
import time

class ConnectionDead(Exception):
    pass

def findofcount(s, n, c):
    x = 0
    p = -1
    while x < c:
        p = s.find(n, p + 1)
        x = x + 1
    return p

class Client:
    def __init__(self, host, port):
        self.inbuf = b''
        self.inlines = []
        self.connected = False
        self.host = host
        self.port = port
        self.connect()

        self.fdindump = open('dataindump', 'w')
        self.fdlndump = open('lineindump', 'w')

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = True
        self.sock.connect((self.host, self.port))
        self.sock.send(b'\x1bbc 1\n')

    def readline(self, block = 0):
        # try to stay connected
        if not self.connected:
            raise ConnectionDead()

        # do not wait because our caller may need to
        # do other things besides wait for data
        self.sock.settimeout(0)

        try:
            data = self.sock.recv(4096)
            self.fdindump.write('%s\n' % data)
            self.fdindump.flush()
            if not data:
                raise ConnectionDead()
            self.inbuf = self.inbuf + data
        except:
            pass

        f9mark = self.inbuf.find(b'\xff\xf9')
        eols = self.inbuf.find(b'\n')
        spbegin = self.inbuf.find(b'\x1b<')

        # use unrealistic values
        if f9mark == -1:
            f9mark = 0x100000
        if eols == -1:
            eols =   0x100000
        if spbegin == -1:
            spbegin =0x100000


        inbuf = self.inbuf

        # do we have a special mark beginning?
        if spbegin < eols and spbegin < f9mark:
            st = time.time()
            count = 1
            x = spbegin + 1
            # optimization shortcut.. obviously, if we have less
            # closing tags than opening tags then there is no way
            # we can find a matching number of closing tags
            oc = inbuf.count(b'\x1b<')
            cc = inbuf.count(b'\x1b>')
            if cc < oc:
                print('cc:%s oc:%s' % (cc, oc))
                print('delta-time:%s' % (time.time() - st))
                return (None, None)
            while x + 1 < len(inbuf) and count > 0:
                if inbuf[x] == 0x1b and inbuf[x + 1] == ord('<'):
                    count += 1
                if inbuf[x] == 0x1b and inbuf[x + 1] == ord('>'):
                    count -= 1
                x = x + 1
            if count > 0:
                print('count:%s' % count)
                # we could not find an end to the sequence of encapculation
                return (None, None)
            print('sequence done')
            # we have found an end to the sequence of encapsulation
            if spbegin > 0:
                # it was an inline sequence
                f9mark = inbuf.find(b'\xff\xf9', x + 1)
                eols = inbuf.find(b'\n', x + 1)
                spbegin = 0x100000
                if f9mark < 0:
                    f9mark = 0x100000
                if eols < 0:
                    eols = 0x100000
            else:
                # it was a block sequence
                line = inbuf[0:x + 3]
                self.inbuf = inbuf[x + 3:]
                return (True, line)

        if f9mark < eols and f9mark < spbegin:
            line = self.inbuf[0:f9mark + 2]
            self.inbuf = self.inbuf[f9mark + 2:]
            self.fdlndump.write('%s\n' % line)
            self.fdlndump.flush()
            return (False, line)

        if eols < f9mark and eols < spbegin:
            line = self.inbuf[0:eols].strip()
            self.inbuf = self.inbuf[eols + 1:]
            self.fdlndump.write('%s\n' % line)
            self.fdlndump.flush()
            return (False, line)
        return (None, None)

    def writeline(self, line):
        if type(line) == str:
            line = bytes(line, 'utf8')
        if not self.connected:
            raise ConnectionDead()
        self.sock.send(line + b'\r\n')
        print('client sent', line)