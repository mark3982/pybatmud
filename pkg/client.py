import socket
import time
import collections
import threading
import time
import os.path

from io import BytesIO

class ConnectionDead(Exception):
    pass

def findofcount(s, n, c):
    x = 0
    p = -1
    while x < c:
        p = s.find(n, p + 1)
        x = x + 1
    return p

def findmulti(s, m, pos = 0):
    lv = None
    for _m in m:
        v = s.find(_m, pos)
        if v > -1 and (lv is None or v < lv):
            lv = v
    return lv

class Client:
    def __init__(self, host, port):
        self.inbuf = b''
        self.inlines = []
        self.connected = False
        self.host = host
        self.port = port

        base = os.path.expanduser('~') + '/pybatmud/'

        # this is used for debugging.. i am leaving it enabled even for
        # production code so that it is possible for users to send me 
        # their data for inspection to find problems, i may make an
        # auto-upload feature for this stuff
        self.fdindump = open(base + 'dbgdump.data', 'w')
        self.fdlndump = open(base + 'dbgdump.line', 'w')
        self.fdbldump = open(base + 'dbgdump.block', 'w')

        self.outque = collections.deque()
        self.sock = None
        self.xsock = [None]

        self.readerthread = threading.Thread(target = Client.reader, args = (self,))
        self.readerthread.setDaemon(True)
        self.readerthread.start()
        self.readerbuf = BytesIO()

    def reader(self):
        # just keep it going
        while True:
            try:
                self.connect()
                self.outque.append((5, None))
            except Exception as e:
                print(e)
                time.sleep(3)
                continue
            try:
                self.reader_inner()
            except Exception as e:
                print(e) 
            # signal connection is dead
            self.outque.append((4, None))


    def reader_inner(self):
        # will need to wrap for socket exception.. close socket if possible.. force reconnect
        chunk = b''
        while True:
            # sleep until valid sock
            if not self.connected:
                time.sleep(1)
                continue
            sock = self.xsock[0]
            if len(chunk) < 2:
                data = sock.recv(4096)
                if not data:
                    return
                self.fdindump.write('%s\n' % data)
                self.fdindump.flush()
                chunk = chunk + data
            # bullcrap "\xff\xfc\x01"
            if chunk[0] == 0xff and chunk[1] == 0xfc:
                chunk = chunk[3:]
                continue
            #if chunk[0] == 0xff and chunk[1] == 0xf9:
            #    chunk = chunk[2:]
            #    continue
            # line
            if not (chunk[0] == 0x1b and (chunk[1] == ord('<') or chunk[1] == ord('>'))):
                chunks = [chunk]

                while findmulti(chunks[-1], (b'\n', b'\x1b<', b'\x1b>', b'\xff\xf9')) is None:
                    data = self.sock.recv(4096)
                    if not data:
                        return
                    self.fdindump.write('%s\n' % data)
                    self.fdindump.flush()
                    chunks.append(data)

                pos = findmulti(chunks[-1], (b'\n', b'\x1b<', b'\x1b>', b'\xff\xf9'))

                tail = chunks[-1][0:pos]

                if chunks[-1][pos] == ord('\n'):
                    slack = chunks[-1][pos + 1:]
                elif chunks[-1][pos] == 0xff:
                    slack = chunks[-1][pos + 2:]
                else:
                    slack = chunks[-1][pos:]
                line = (b''.join(chunks[0:-1]) + tail).strip(b'\r')
                if chunks[-1][pos] == ord('\n'):
                    self.outque.append((0, line))
                    self.fdbldump.write('l:%s\n' % line)
                    self.fdbldump.flush()
                elif chunks[-1][pos] == 0xff:
                    self.outque.append((3, line))
                    self.fdbldump.write('p:%s\n' % line)
                    self.fdbldump.flush()                    
                else:
                    self.outque.append((1, line))
                    self.fdbldump.write('c:%s\n' % line)
                    self.fdbldump.flush()
                if len(slack) > 0:
                    chunk = slack
                else:
                    chunk = b''
                continue
            # block
            count = 0
            tagi = 0
            closedout = False
            # remove crazy ass closing tag... what the mother fuck is this shit...
            if chunk[1] == ord('>'):
                # for gods sake.. why.. is the server bugged?
                chunk = chunk[4:]
                continue
            while True:
                # is it a one byte code or multiple byte code
                if chunk[3] < ord('0') or chunk[3] > ord('9'):
                    tsz = 3
                    isz = 2
                else:
                    tsz = 4
                    isz = 2
                tag = chunk[0:tsz]
                etag =  b'\x1b>' + tag[isz:]
                if chunk.find(etag) > -1:
                    tagi = chunk.find(etag)
                    block = chunk[0:tagi + tsz]
                    slack = chunk[tagi + tsz:]
                    self.fdbldump.write('b:%s\n' % block)
                    self.fdbldump.flush()
                    self.outque.append((2, block))
                    if len(slack) > 0:
                        chunk = slack
                    else:
                        chunk = b''
                    break
                data = sock.recv(4096)
                if not data:
                    return
                self.fdindump.write('%s\n' % data)
                self.fdindump.flush()
                chunk = chunk + data
            continue

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.sock.send(b'\x1bbc 1\n')
        self.xsock[0] = self.sock
        self.connected = True
        print('CONNECTED', self, self.sock)

    def readitem(self):
        if len(self.outque) > 0:
            return self.outque.popleft()
        return (None, None)

    def peekitem(self):
        if len(self.outque) > 0:
            return self.outque[0]
        return (None, None)

    def __OLD__readline(self, block = 0):
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
                self.fdbldump.write('%s\n' % line)
                self.fdbldump.flush()
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
        try:
            self.sock.send(line + b'\r\n')
        except Exception as e:
            print(e)