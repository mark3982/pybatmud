import time
import pprint

from pkg.client import Client
from pkg.client import ConnectionDead
from pkg.dprint import dprint

class Priority:
    Monitor         =       100
    High            =       75
    Medium          =       50
    Normal          =       50
    Low             =       25

class Game:
    _instance = None

    def __init__(self):
        Game._instance = self
        self.connected = False
        self.ereg = {}

    def instance():
        return Game._instance

    def stripofescapecodes(self, line):
        line = line.decode('utf8', 'replace')

        parts = line.split('\x1b')

        line = []

        line.append(parts[0])

        for x in range(1, len(parts)):
            part = parts[x]
            part = part[part.find('m') + 1:]
            line.append(part)

        return ''.join(line)

    def start(self):
        self.c = Client('bat.org', 23)

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
        dprint('command', command)
        self.c.writeline(command)

    def tick(self, block = 10):
        while True:
            # read a single line
            try:
                xtype, line = self.c.readitem()
            except ConnectionDead:
                if self.connected:
                    self.connected = False
                    self.pushevent('disconnected')
                    # try to reconnect at least once
                    self.activate()
            if xtype is None:
                break
            if xtype == 0:
                self.pushevent('lineunknown', line)
                continue
            if xtype == 1:
                self.pushevent('chunkunknown', line)
                continue
            if xtype == 2:
                self.pushevent('blockunknown', line)
                continue
            if xtype == 3:
                # catch this crap early.. if i find out i need it then
                # maybe i will just make a completely new event if --kmcg
                if len(line.strip()) > 0:
                    self.pushevent('prompt', line)
                continue
            if xtype == 4:
                self.pushevent('disconnected')
                continue
            if xtype == 5:
                self.pushevent('connected')
                continue

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
            if dt > 0.5:
                # give some kind of warning.. likely the user has experienced
                # the UI being non-responsive, or they would have if they were
                # doing something with it so let them know that something may
                # be wrong.. also helpful for developers to see their plugin
                # is taking a bit too longer to perform it's action
                print('[warning] call %s seconds for %s!' % (dt, cb[0]))
            if type(res) == tuple:
                if res[0] is True:
                    return res
            if res is True:
                return res