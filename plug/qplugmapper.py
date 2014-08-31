import os
import os.path
import struct
import array
import time
from pprint import pprint
import tracemalloc

from PyQt4 import QtCore
from PyQt4 import QtGui
from pkg.qsubwindow import QSubWindow
from pkg.dprint import dprint

class QPlugMapper(QSubWindow):
    """Provides QT widget login window.

    This provides the login needed to enter into the game.
    """
    def __init__(self, pwin, game):
        super().__init__(pwin)
        self.pwin = pwin
        self.game = game

        if not os.path.exists('./mapper'):
            os.makedirs('./mapper')

        # we only appear during the login sequence
        game.registerforevent('whereami', self.event_whereami)
        game.registerforevent('map', self.event_map)
        game.registerforevent('command', self.event_command)
        game.registerforevent('batmapper', self.event_batmapper)
        game.registerforevent('mobdetected', self.event_mobdetected)
        game.registerforevent('connected', self.event_connected)

        self.gmap = {}
        # now handled in event_connected method
        #self.whereami_intercept = False
        #self.lastxmap = None
        #self.lastcord = None

        self.resize(200, 200)
        self.show()

        self.bzoomout = QtGui.QPushButton(self)
        self.bzoomin = QtGui.QPushButton(self)

        self.bzoomout.move(0, 0)
        self.bzoomout.resize(10, 10)
        self.bzoomout.setText('-')
        self.bzoomin.move(10, 0)
        self.bzoomin.resize(10, 10)
        self.bzoomin.setText('+')

        self.bzoomout.show()
        self.bzoomin.show()

        self.bzoomout.clicked.connect(self.zoomout)
        self.bzoomin.clicked.connect(self.zoomin)
        '''
        ,--------------------------[ Terrain types ]--------------------------.
        | !   Mountain Peak                 #   Ruins                         |
        | %   Special Location              +   Crossing                      |
        | ,   Trail                         -   Road                          |
        | .   Plains                        =   Bridge                        |
        | ?   Scenic Location               @   Flowing Lava                  |
        | C   Player City                   F   Deep Forest                   |
        | H   Highlands                     L   Lava Lake                     |
        | R   Deep River                    S   Shallows                      |
        | V   Volcano                       ^   Mountain                      |
        | b   Beach                         c   City                          |
        | d   Desert                        f   Forest                        |
        | h   Hills                         i   Ice                           |
        | j   Jungle                        l   Lake                          |
        | r   River                         s   Swamp                         |
        | t   Tundra                        v   Valley                        |
        | w   Waterfall                     x   Badlands                      |
        | y   Fields                        z   Shore                         |
        | ~   Sea                                                             |
        `---------------------------------------------------------------------'
        '''

        qc = QtGui.QColor
        self.landcolor = {
            '|':    qc(0xa0, 0xa0, 0xa0),
            '\\':   qc(0xa0, 0xa0, 0xa0),
            '/':    qc(0xa0, 0xa0, 0xa0),
            '#':    qc(0xff, 0xff, 0xff),
            '+':    qc(0xa0, 0xa0, 0xa0),
            '-':    qc(0x33, 0x33, 0x33),
            '=':    qc(0x33, 0x33, 0x33),
            '@':    qc(0xff, 0x00, 0x00),
            'F':    qc(0x99, 0xff, 0x99),
            'L':    qc(0xff, 0x00, 0x00),
            'S':    qc(0x99, 0x99, 0xff),
            '^':    qc(0x11, 0x11, 0x11),
            'c':    qc(0xff, 0xff, 0xff),
            'f':    qc(0x99, 0xff, 0x99),
            'i':    qc(0xdd, 0xdd, 0xff),
            'l':    qc(0x99, 0x99, 0xff),
            's':    qc(0x88, 0xdd, 0xbb),
            'v':    qc(0x88, 0xdd, 0xbb),
            'x':    qc(0x99, 0x33, 0x55),
            'z':    qc(0xdd, 0xdd, 0xff),
            '!':    qc(0x44, 0x44, 0x44),
            '%':    qc(0xff, 0xff, 0xff),
            ',':    qc(0x88, 0x88, 0x88),
            '.':    qc(0x99, 0xff, 0x99),
            '?':    qc(0xff, 0xff, 0xff),
            'C':    qc(0xff, 0xff, 0xff),
            'H':    qc(0x9d, 0x9a, 0x41),
            'R':    qc(0x00, 0x00, 0xff),
            'V':    qc(0xff, 0x00, 0x00),
            'b':    qc(0xde, 0xd7, 0x25),
            'd':    qc(0xff, 0xf6, 0x03),
            'h':    qc(0x8e, 0x8a, 0x29),
            'j':    qc(0x00, 0xff, 0x00),
            'r':    qc(0x00, 0x00, 0xff),
            't':    qc(0xee, 0xee, 0xee),
            'w':    qc(0x00, 0x00, 0xff),
            'y':    qc(0xb8, 0xbf, 0x67),
            '~':    qc(0x00, 0x00, 0xff)
        }

        self.toflushtodisk = set()
        self.notes = []

        if os.path.exists('./mapper/notes'):
            fd = open('./mapper/notes', 'r')
            lines = fd.readlines()
            fd.close()
            for line in lines:
                line = line.strip()
                if len(line) < 1:
                    continue
                parts = line.split('\x19')
                self.notes.append([int(parts[0]), int(parts[1]), parts[2], None])

        self.csz = 1

        self.batmapload()

        self.amap = {
            'n':    (0, -1, 0),
            's':    (0, 1, 0),
            'e':    (1, 0, 0),
            'w':    (-1, 0, 0),
            'ne':   (1, -1, 0),
            'nw':   (-1, -1, 0),
            'se':   (1, 1, 0),
            'sw':   (-1, 1, 0),
            'u':    (0, 0, 1),
            'd':    (0, 0, -1),
        }

    def event_connected(self, event):
        self.whereami_intercept = False
        self.lastxmap = None
        self.lastcord = None
        self.lastbatmapper = None
        self.wasoutside = None
        self.lastbatmapper = None

    def paintEvent(self, event):
        if self.lastbatmapper is not None:
            self.renderbatmap()
        else:
            self.rendermap()

    def zoomout(self):
        self.csz = self.csz * 0.5
        self.update()
    def zoomin(self):
        self.csz = self.csz * 2
        self.update()

    def notesflush(self):
        dprint('notes flush')
        fd = open('./mapper/notes', 'w')
        for note in self.notes:
            line = '%s\x19%s\x19%s' % (note[0], note[1], note[2])
            fd.write('%s\n' % line)
        fd.close()

    def renderbatmap(self):
        p = QtGui.QPainter()
        p.begin(self)
        p.setPen(QtCore.Qt.white)
        p.setFont(QtGui.QFont('consolas', 8))

        thiszone = self.lastbatmapper[0]
        thisroom = self.lastbatmapper[1]

        batmap = self.batmap

        cx = self.width() * 0.5
        cy = self.height() * 0.5

        bugs = []

        bug = (thiszone, thisroom, cx, cy, 0xffffff)
        bugs.append(bug)

        visited = set()
        visited.add((thiszone, thisroom))

        om = {
            'n':    (+0, -1),
            's':    (+0, +1),
            'e':    (+1, +0),
            'w':    (-1, +0),
            'ne':   (+1, -1),
            'se':   (+1, +1),
            'sw':   (-1, +1),
            'nw':   (-1, -1),
        }

        scale = 10
        pad = 1

        while len(bugs) > 0:
            _bugs = []
            for thiszone, thisroom, cx, cy, color in bugs:
                # draw bug
                p.setPen(QtGui.QColor(color))
                p.drawRect(cx + pad, cy + pad, scale - pad * 2, scale - pad * 2)

                zone = batmap[thiszone]
                room = zone[thisroom]

                cango = set()
                havemoved = set()
                for location, move in room['forward']:
                    cango.add((location, move))
                    havemoved.add(move)
                for location, move in room['backward']:
                    cango.add((location, move))
                    havemoved.add(move)
                notmoved = set()
                for move in room['moves']:
                    if move not in havemoved:
                        notmoved.add(move)
                # create children
                for location, move in cango:
                    if location in visited:
                        # dont go to the same place twice
                        continue
                    if move in om:
                        off = om[move]
                        _cx = cx + off[0] * scale
                        _cy = cy + off[1] * scale
                    else:
                        continue
                    _bugs.append((location[0], location[1], _cx, _cy, 0x99ff99))
                    visited.add(location)
            bugs = _bugs

        p.end()

    def rendermap(self):
        if self.lastcord is None:
            return
        p = QtGui.QPainter()
        p.begin(self)
        p.setPen(QtCore.Qt.black)
        p.setFont(QtGui.QFont('consolas', 8))

        csz = self.csz

        w = self.width() / csz
        h = self.height() / csz

        w = int(w * 0.5)
        h = int(h * 0.5)

        cord = self.lastcord

        left = cord[0] - w
        right = cord[0] + w
        top = cord[1] - h
        bottom = cord[1] + h

        ox = (left & 0xff) * csz
        oy = (top & 0xff) * csz

        csx = left >> 8
        csy = top >> 8
        clx = right >> 8
        cly = bottom >> 8

        x = -ox
        for cx in range(csx, clx + 1):
            y = -oy
            for cy in range(csy, cly + 1):
                chunk = self.gmapgetchunk(cx, cy)
                p.drawImage(QtCore.QRect(x, y, 256 * csz, 256 * csz), chunk, QtCore.QRect(1, 1, 256, 256))
                y = y + 256 * csz
            x = x + 256 * csz

        p.end()

        for note in self.notes:
            # is note in our view?
            nx = note[0]
            ny = note[1]
            msg = note[2]
            w = note[3]

            if nx >= left and nx <= right and ny >= top and ny <= bottom:
                if w is None:
                    # create the note
                    w = QtGui.QLabel(self)
                    w.setText(msg)
                    w.setStyleSheet('font-family: Arial; font-size: 8pt; background-color: rgba(99, 99, 99, 44);')
                    w.show()
                    note[3] = w
                # position the note
                w.move((nx - cord[0]) * csz + self.width() * 0.5, (ny - cord[1]) * csz + self.height() * 0.5)
            else:
                if w is not None:
                    # destroy the note
                    w.hide()
                    w.setParent(None)
    '''
        I use a 256x256 chunk because it seemed optimal, and when I start
        writing code to load and unload chunks it will be 
    '''
    def gmapset(self, x, y, v):
        cx = x >> 8
        cy = y >> 8
        # ensure the chunk is loaded (if not it loads it)
        self.gloadchunk(cx, cy) 
        lx = x & 0xff
        ly = y & 0xff
        #print('lx:%s ly:%s max:%s len:%s' % (lx, ly, 9 * 11, len(self.gmap[cx][cy])))
        #self.gmap[cx][cy][ly * 256 + lx] = v
        self.gmap[cx][cy].setPixel(lx, ly, v)
        self.toflushtodisk.add((cx, cy))

    def gflush(self):
        """Write all modified chunks out to disk.
        """
        for cx, cy in self.toflushtodisk:
            #fd = open('./mapper/%s_%s' % (cx, cy), 'wb')
            #chunk = self.gmap[cx][cy]
            #for x in range(0, len(chunk)):
            #    fd.write(struct.pack('B', chunk[x]))
            #fd.close()
            self.gmap[cx][cy].save('./mapper/%s_%s.png' % (cx, cy))

    def gloadchunk(self, cx, cy):
        """Loads a chunk into memory, or creates a fresh one.
        """
        if cx not in self.gmap:
            self.gmap[cx] = {}
        if cy in self.gmap[cx]:
            return
        mapfile = './mapper/%s_%s.png' % (cx, cy)
        if not os.path.exists(mapfile):
            #self.gmap[cx][cy] = [0] * (256 * 256)
            #self.gmap[cx][cy] = array.array('B', [0 for x in range(256 * 256)])
            #QtGui.QImage.Format_Indexed8
            img = QtGui.QImage(256, 256, QtGui.QImage.Format_Indexed8)
            self.gmap[cx][cy] = img
            img.setColorCount(256)
            img.setColor(0, 0)
            for k in self.landcolor:
                v = self.landcolor[k]
                img.setColor(ord(k), v.rgba())
            img.fill(0)
            return
        #fd = open(mapfile, 'rb')
        #data = fd.read()
        #fd.close()
        #chunk = array.array('B')
        self.gmap[cx][cy] = QtGui.QImage()
        self.gmap[cx][cy].load(mapfile)
        #if len(data) < 256 * 256:
        #    print('warning: chunk disk data less than expected!')
        #    # just drop the chunk to recover
        #    #self.gmap[cx][cy] = [0] * (256 * 256)
        #    #self.gmap[cx][cy] = array.array('B', [0 for x in range(256 * 256)])
        #    self.gmap[cx][cy] = QtGui.QImage(256, 256, QtGui.QImage.Format_Indexed8)
        #    self.gmap[cx][cy].fill(0)
        #    return
        #for i in range(0, len(data)):
        #    chunk.append(data[i])
        #self.gmap[cx][cy] = QtGui.QImage(data, 256, 256, QtGui.QImage.Format_Indexed8)
        #self.gmap[cx][cy] = chunk

    def gmapgetchunk(self, cx, cy):
        self.gloadchunk(cx, cy)
        return self.gmap[cx][cy]

    def gmapget(self, x, y):
        cx = x >> 8
        cy = y >> 8
        # ensure the chunk is loaded (if not it loads it)
        self.gloadchunk(cx, cy) 
        lx = x & 0xff
        ly = y & 0xff
        #return self.gmap[cx][cy][ly * 256 + lx]
        return self.gmap[cx][cy].pixelIndex(lx, ly)

    def processmap(self, xmap, lcords, gcords):
        # 19 wide       [9]
        # 11 tall       [5]
        #cords = (lcords[0] + gcords[0], lcords[1] + gcords[1])
        cords = gcords

        gmap = self.gmap
        for y in range(0, 11):
            for x in range(0, 19):
                gx = cords[0] - (9 - x)    # global offset for unit
                gy = cords[1] - (5 - y)    # global offset for unit
                if xmap[y][x] == ' ':
                    continue
                # if not in land color.. its prolly a monster, player, ..etc
                if xmap[y][x] not in self.landcolor:
                    continue
                if self.gmapget(gx, gy) != 0:
                    continue
                self.gmapset(gx, gy, ord(xmap[y][x]))
        self.gflush()
        self.update()

    def event_command(self, event, command):
        parts = command.split(' ')

        if len(parts) > 0 and parts[0] == 'mapper':
            if len(parts) > 1 and parts[1] == 'totals':
                zonecount = 0
                roomcount = 0
                for zone in self.batmap:
                    zonecount += 1
                    for room in zone:
                        roomcount += 1
                self.game.pushevent('lineunknown', bytes('\x1b#ffffffmapper: tracking %s zones and %s rooms!' % (zonecount, roomcount), 'utf8'))
            if len(parts) > 1 and parts[1] == 'addnote':
                note = ' '.join(parts[2:])
                if self.lastbatmapper is None:
                    if self.lastcord is not None:
                        cx = self.lastcord[0]
                        cy = self.lastcord[1]
                        self.notes.append([cx, cy, note, None])
                        self.notesflush()
                        # specify to drop propagation of event and not to forward command
                        self.game.pushevent('lineunknown', b'mapper: added note to world')
                        return (True, True)
                else:
                    zonename = self.lastbatmapper[0]
                    roomname = self.lastbatmapper[1]
                    room = self.batmap[zonename][roomname]
                    if 'notes' not in room:
                        room['notes'] = []
                    room['notes'].append(note)
                    self.game.pushevent('lineunknown', b'mapper: added note to dungeon')
            if len(parts) > 1 and parts[1] == 'navtoroom':
                if len(parts) < 3:
                    self.game.pushevent('lineunknown', b'mapper: need target room name')
                else:
                    pass

            if len(parts) > 1 and parts[1] == 'tracemalloc':
                ss = tracemalloc.take_snapshot()
                top_stats = ss.statistics('lineno')
                for stat in top_stats[0:30]:
                    print(stat)

            if len(parts) > 1 and parts[1] == 'listnotes':
                if self.lastbatmapper is None:
                    self.game.pushevent('lineunknown', b'mapper: not inside dungeon (look at map for world maybe..)')
                else:
                    zonename = self.lastbatmapper[0]
                    zone = self.batmap[zonename]
                    for roomname in zone:
                        room = zone[roomname]
                        if 'notes' in room:
                            self.game.pushevent('lineunknown', b'  ' + bytes(roomname, 'utf8'))
                            for note in room['notes']:
                                self.game.pushevent('lineunknown', b'    ' + bytes(note, 'utf8'))

            if len(parts) > 1 and parts[1] == 'findout':
                self.game.pushevent('lineunknown', b'\x1b#ffffffmmapper: Entrance And/Or Exit Shortest Path')
                goal = self.findpath(self.goalcheck_enterorexit)
                for history, extra in goal:
                    zonename = history[-1][0]
                    roomname = history[-1][1]
                    zone = self.batmap[zonename]
                    room = zone[roomname]
                    if len(room['entered']) > 0:
                        prefix = []
                        for txt in room['entered']:
                            prefix.append('%s' % txt)
                        prefix = b'   (out)' + bytes('|'.join(prefix), 'utf8')
                        self.game.pushevent('lineunknown', prefix)
                    if len(room['exited']) > 0:
                        prefix = []
                        for txt in room['exited']:
                            prefix.append('%s' % txt)
                        prefix = b'   (in)' + bytes('|'.join(prefix), 'utf8')
                        self.game.pushevent('lineunknown', prefix)
                    line = []
                    # drop the first node
                    history = history[1:]
                    for zonename, roomname, action in history:
                        line.append('%s->' % action)
                    line = bytes(''.join(line), 'utf8')
                    self.game.pushevent('lineunknown', b'     \x1b#99ff99m->' + line)

            if len(parts) > 1 and parts[1] == 'findnew':
                self.game.pushevent('lineunknown', b'\x1b#ffffffmmapper: Unexplored Rooms')
                #gg = self.findpath(None)
                gg = {}
                def __goalcheck_newcheck(zonename, roomname, _, coff):
                    zone = self.batmap[zonename]
                    room = zone[roomname]

                    amap = self.amap

                    havedonemoves = set()
                    for zoneandroom, move in room['backward']:
                        havedonemoves.add(move)
                    for zoneandroom, move in room['forward']:
                        havedonemoves.add(move)

                    #dprint('goal check', zonename, roomname, havedonemoves, room['moves'])

                    for move in room['moves']:
                        if move not in havedonemoves:
                            if coff[0] is not None and move in amap:
                                ggoff = amap[move]
                                cx = coff[0] + ggoff[0]
                                cy = coff[1] + ggoff[1]
                                cz = coff[2] + ggoff[2]
                                if (cx, cy, cz) in gg:
                                    # nope, we been here before
                                    continue
                                return (cx, cy, cz)
                            else:
                                return (None, None, None)
                    return False

                goal = self.findpath(__goalcheck_newcheck)
                for x in range(0, min(len(goal), 15)):
                    dprint('goal', goal[x][1])

                    history = goal[x][0]
                    tx, ty, tz = goal[x][1]

                    endzonename = history[-1][0]
                    endroomname = history[-1][1]

                    line = []
                    # drop the first node
                    for zonename, roomname, action in history:
                        line.append('%s->' % action)

                    # figure out which moves have never been made
                    goalroom = self.batmap[endzonename][endroomname]

                    havedonemoves = set()

                    for zoneandroom, move in goalroom['backward']:
                        havedonemoves.add(move)

                    for zoneandroom, move in goalroom['forward']:
                        havedonemoves.add(move)

                    sub = []
                    for move in goalroom['moves']:
                        if move not in havedonemoves:
                            if tx is not None and move in self.amap:
                                ggoff = self.amap[move]
                                cx = tx + ggoff[0]
                                cy = ty + ggoff[1]
                                cz = tz + ggoff[2]
                                if (cx, cy, cz) in gg:
                                    # nope, we been here before
                                    continue                            
                            sub.append(move)

                    if len(sub) > 0:
                        line.append('\x1b#9999ddm[%s]' % '|'.join(sub))

                        line = bytes(''.join(line), 'utf8')
                        self.game.pushevent('lineunknown', b'     \x1b#99ff99m->' + line)

            return (True, True)

    def goalcheck_enterorexit(self, zone, xid, gg, coff):
        zone = self.batmap[zone]
        room = zone[xid]
        if len(room['entered']) > 0 or len(room['exited']) > 0:
            return True
        return False

    def findpath(self, goalcheck, usegg = True):
        """This will find all paths that satisfy the goal check function provided.

        This will find all paths that satisfy the goal check function provided.

        goalcheck    - shall be a function taking the appropriate arguments
        usegg        - uses geometric grid to determine if rooms have been visited
        """
        if self.lastbatmapper is None:
            self.game.pushevent('lineunknown', b'mapper: not inside zone - assuming your in the world (try moving)!')
            return []
        thiszone = self.lastbatmapper[0]
        zone = self.batmap[thiszone]
        thisxid = self.lastbatmapper[1]
        goal = []
        visited = set()
        gg = set()
        gg = {}
        gg[(0, 0, 0)] = (thiszone, thisxid)
        bugs = []
        bugs.append((thiszone, thisxid, [(thiszone, thisxid, 'start')], 0, 0, 0))
        amap = self.amap
        if goalcheck is not None:
            res = goalcheck(thiszone, thisxid, gg, (0, 0, 0))
            if res is not False and res is not None:
                goal.append(([(thiszone, thisxid, 'start')], res))
        visited.add((thiszone, thisxid))
        while len(bugs) > 0:
            _bugs = []
            # iterate through parents letting them create child bugs
            for thiszone, thisxid, history, tx, ty, tz in bugs:
                zone = self.batmap[thiszone]
                room = zone[thisxid]
                forward = room['forward']
                backward = room['backward']
                _combined = set()
                for action in forward:
                    _combined.add(action)
                for action in backward:
                    _combined.add(action)

                for action in _combined:
                    tozone, toxid = action[0]
                    if (tozone, toxid) in visited:
                        # if we been here before dont go back to it
                        continue
                    tomove = action[1]
                    # create new child bug that inherits parent history
                    nhistory = history + [(tozone, toxid, tomove)]
                    if tx is not None and tomove in amap:
                        ggoff = amap[tomove]
                        cx = tx + ggoff[0]
                        cy = ty + ggoff[1]
                        cz = tz + ggoff[2]
                        if (cx, cy, cz) in gg:
                            # it seems most dungeons do not have a straight forward
                            # geometric grid representation for vertical layers which
                            # means this fails to eliminate all visited rooms.. so we
                            # just have to be aware of it
                            pass
                        gg[(cx, cy, cz)] = (tozone, toxid)
                    else:
                        cx = None
                        cy = None
                        cz = None
                        dprint('LOST GEO GRID with %s:%s' % (tx, tomove))

                    _bugs.append((tozone, toxid, nhistory, cx, cy, cz))
                    if goalcheck is not None:
                        res = goalcheck(tozone, toxid, gg, (cx, cy, cz))
                        if res is not False and res is not None:
                            goal.append((nhistory, res))
                    visited.add((tozone, toxid))
            # parent die and children become parents
            bugs = _bugs
        self.game.pushevent('lineunknown', bytes('  Searched %s/%s/%s Rooms' % (len(visited), len(zone), len(gg)), 'utf8'))
        # should have zero or more goals
        if goalcheck is None:
            return gg
        else:
            return goal

    def batmapflush(self):
        fd = open('./mapper/batmap', 'w')
        #pprint(self.batmap, fd)
        fd.write('%s' % self.batmap)
        fd.close()

    def batmapload(self):
        if os.path.exists('./mapper/batmap'):
            fd = open('./mapper/batmap', 'r')
            data = fd.read()
            if len(data) > 0:
                self.batmap = eval(data)
            else:
                self.batmap = {}
            fd.close()
        else:
            self.batmap = {}

    def event_mobdetected(self, event, mob):
        if self.lastbatmapper is not None:
            self.game.pushevent('lineunknown', b'\x1b#222222m* stored mob to dungeon room -> ' + bytes(mob, 'utf8'))
            lastzone = self.lastbatmapper[0]
            lastroom = self.lastbatmapper[1]
            if 'seenmobs' not in self.batmap[lastzone][lastroom]:
                self.batmap[lastzone][lastroom]['seenmobs'] = set()
            self.batmap[lastzone][lastroom]['seenmobs'].add(mob)

    def event_batmapper(self, event, thiszone, xid, lastmove, desc, moves):

        dprint('thiszone', thiszone)
        dprint('thisroom', xid)
        dprint('lastmove', lastmove)
        dprint('desc', desc[0:10].replace('\n', '').replace('\r', ''))
        dprint('moves', moves)

        _moves = moves.split(',')
        moves = set()
        mi = {
            'n':    's',
            's':    'n',
            'e':    'w',
            'w':    'e',
            'u':    'd',
            'd':    'u',
            'nw':   'se',
            'ne':   'sw',
            'sw':   'ne',
            'se':   'nw',
        }
        m = {
            'north': 'n', 'northeast': 'ne', 'east': 'e', 'southeast': 'se',
            'south': 's', 'southwest': 'sw', 'west': 'w', 'northwest': 'nw',
            'up': 'u', 'down': 'd'
        }
        for move in _moves:
            if move in m:
                moves.add(m[move])
            else:
                moves.add(move)

        # normalize it
        if lastmove in m:
            lastmove = m[lastmove]
            lastmoveinvert = mi[lastmove]
        else:
            lastmoveinvert = None

        if thiszone not in self.batmap:
            self.batmap[thiszone] = {}
        zone = self.batmap[thiszone]

        if xid not in zone:
            zone[xid] = {}
            zone[xid]['forward'] = set()
            zone[xid]['backward'] = set()
            zone[xid]['desc'] = None
            zone[xid]['moves'] = None
            zone[xid]['entered'] = set()
            zone[xid]['exited'] = set()
            zone[xid]['seenmobs'] = set()

        if self.lastbatmapper is not None:
            lastzone = self.lastbatmapper[0]
            lastxid = self.lastbatmapper[1]
            if lastzone == thiszone:
                # add backward link
                dprint('lastmoveinvert:%s lastmove:%s' % (lastmoveinvert, lastmove))
                zone[xid]['backward'].add(((lastzone, lastxid), lastmoveinvert))
                # add forward link
                zone[lastxid]['forward'].add(((thiszone, xid), lastmove))
            else:
                # mark we entered here
                zone[xid]['entered'].add(lastzone)
                zone[xid]['backward'].add(((lastzone, lastxid), lastmoveinvert))
                # mark we exited here
                self.batmap[lastzone][lastxid]['exited'].add(thiszone)
                self.batmap[lastzone][lastxid]['forward'].add(((thiszone, xid), lastmove))
        else:
            if self.wasoutside is True:
                # we came from the world
                zone[xid]['entered'].add('world')

        if zone[xid]['desc'] is not None and zone[xid]['desc'] != desc:
            # well.. we must be in a maze.. or something crazy
            self.game.pushevent('lineunknown', b'\x1b#ff9999mwarning: \x1b#ffffffmmapper plugin detected possible maze!')

        zone[xid]['desc'] = desc
        zone[xid]['moves'] = moves

        dprint('added entry zone:%s xid:%s moves:%s' % (thiszone, xid, moves))

        self.wasoutside = False
        self.lastbatmapper = (thiszone, xid, lastmove, desc, moves)

        self.batmapflush()

        self.update()

    def event_map(self, event, xmap):
        if self.lastbatmapper is not None:
            lbm = self.lastbatmapper
            self.batmap[lbm[0]][lbm[1]]['exited'].add('world')

        self.game.command('whereami')
        self.whereami_intercept = True
        self.lastxmap = xmap

    def event_whereami(self, event, area, zone, cont, lcords, gcords):
        self.lastcord = gcords
        if self.whereami_intercept:
            if zone == None:
                # not insize a zone (lcords and gcords accurate)
                if self.lastbatmapper is not None:
                    # mark this unit of the zone as an exit
                    self.batmap[self.lastbatmapper[0]][self.lastbatmapper[1]]['exited'].add('world')
                self.lastbatmapper = None
                self.processmap(self.lastxmap, lcords, gcords)
                self.wasoutside = True
            else:
                # generally if we get this during our interception it
                # means we are in an area with a map so we can stop tracking
                # using the batmap extension and it likely is not even being
                self.lastbatmapper = None

            self.whereami_intercept = False
            return True, True

        