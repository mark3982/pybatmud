import time

from pkg.client import Client
from pkg.client import ConnectionDead

class Priority:
    Monitor         =       100
    High            =       75
    Medium          =       50
    Normal          =       50
    Low             =       25

class Game:
    def __init__(self):
        self.c = Client('bat.org', 23)
        self.connected = False
        self.ereg = {}

    def activate(self):
        self.c.connect()
        # if successful then let all listeners
        # know that we have an established connection
        self.pushevent('connected')

    def registerforevent(self, event, cb, priority = Priority.Medium):
        """Register a callback to handle the event.
        """
        if event not in self.ereg:
            self.ereg[event] = []
        # insert into list with regard to priority
        cbs = self.ereg[event]
        x = 0
        for x in range(0, len(cbs) + 1):
            if x >= len(cbs):
                # append to end of list
                cbs.append((cb, priority))
                return
            if priority > cbs[x][1]:
                break
        cbs.insert(x, (cb, priority))

    def command(self, command):
        try:
            self.c.writeline(command)
        except ConnectionDead:
            if self.connected:
                # only raise event once until connection is
                # re-established
                self.connected = False
                self.pushevent('disconnected')
                # try to reconnect at least once
                self.activate()

    def tick(self, block = 10):
        while True:
            # read a single line
            try:
                block, line = self.c.readline()
            except ConnectionDead:
                if self.connected:
                    self.connected = False
                    self.pushevent('disconnected')
                    # try to reconnect at least once
                    self.activate()
            if line is None:
                break
            if not block:
                # a line which may contain batmud client extension sequences
                self.pushevent('rawunknown', line)
            else:
                # a block is a batmud client extension block of sequences
                self.pushevent('blockunknown', line)

    def pushevent(self, event, *args):
        """Push the event to any registered callbacks.
        """
        if event not in self.ereg:
            return
        # call in priority ordering (highest first)
        for x in range(0, len(self.ereg[event])):
            cb = self.ereg[event][x]
            st = time.time()
            res = cb[0](event, *args)
            dt = time.time() - st
            #print('call %s seconds for %s' % (dt, cb[0]))
            if res is True:
                # callback has specified to not forward
                # the event any further and we shall drop
                # it and not let it propagate
                return