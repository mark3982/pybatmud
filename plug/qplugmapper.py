import os
import os.path
import struct

from PyQt4 import QtCore
from PyQt4 import QtGui
from pkg.qsubwindow import QSubWindow

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

        self.gmap = {}
        self.whereami_intercept = False
        self.lastxmap = None
        self.lastcord = None

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

    def paintEvent(self, event):
        self.rendermap()

    def zoomout(self):
        pass
    def zoomin(self):
        pass

    def event_command(self, event, command):
        parts = command.split(' ')

        if len(parts) > 0 and parts[0] == 'mapper':
            if len(parts) > 1 and parts[1] == 'addnote':
                note = ' '.join(parts[2:])
                if self.lastcord is not None:
                    cx = self.lastcord[0]
                    cy = self.lastcord[1]
                    self.notes.append([cx, cy, note, None])

    def rendermap(self):
        if self.lastcord is None:
            return
        p = QtGui.QPainter()
        p.begin(self)
        p.setPen(QtCore.Qt.black)
        p.setFont(QtGui.QFont('consolas', 12))

        csz = 12

        w = self.width() / csz
        h = self.height() / csz

        w = int(w * 0.5)
        h = int(h * 0.5)

        cord = self.lastcord

        left = cord[0] - w
        right = cord[0] + w
        top = cord[1] - h
        bottom = cord[1] + h

        for y in range(-h, h):
            for x in range(-w, w):
                gx = x + cord[0]
                gy = y + cord[1]
                v = self.gmapget(gx, gy)

                py = (y + h) * csz
                px = (x + w) * csz

                v = chr(v) 

                if v in self.landcolor:
                    p.setPen(self.landcolor[v])
                p.drawText(px, py, v)
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
                    w.setStyleSheet('font-family: Arial; font-size: 8pt;')
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
        self.gmap[cx][cy][ly * 256 + lx] = v
        self.toflushtodisk.add((cx, cy))

    def gflush(self):
        """Write all modified chunks out to disk.
        """
        for cx, cy in self.toflushtodisk:
            fd = open('./mapper/%s_%s' % (cx, cy), 'wb')
            chunk = self.gmap[cx][cy]
            for x in range(0, len(chunk)):
                fd.write(struct.pack('B', chunk[x]))
            fd.close()

    def gloadchunk(self, cx, cy):
        """Loads a chunk into memory, or creates a fresh one.
        """
        if cx not in self.gmap:
            self.gmap[cx] = {}
        if cy in self.gmap[cx]:
            return
        mapfile = './mapper/%s_%s' % (cx, cy)
        if not os.path.exists(mapfile):
            print('new chunk')
            self.gmap[cx][cy] = [0] * (256 * 256)
            return
        fd = open(mapfile, 'rb')
        data = fd.read()
        fd.close()
        chunk = []
        if len(data) < 256 * 256:
            print('warning: chunk disk data less than expected!')
            # just drop the chunk to recover
            self.gmap[cx][cy] = [0] * (256 * 256)
            return
        for i in range(0, len(data)):
            chunk.append(data[i])
        self.gmap[cx][cy] = chunk

    def gmapget(self, x, y):
        cx = x >> 8
        cy = y >> 8
        # ensure the chunk is loaded (if not it loads it)
        self.gloadchunk(cx, cy) 
        lx = x & 0xff
        ly = y & 0xff
        return self.gmap[cx][cy][ly * 256 + lx]

    def processmap(self, xmap, lcords, gcords):
        print('processing map')
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
                print(xmap[y][x], end='')
                self.gmapset(gx, gy, ord(xmap[y][x]))
        print('')
        self.gflush()
        self.update()

    def event_map(self, event, xmap):
        self.game.command('whereami')
        self.whereami_intercept = True
        self.lastxmap = xmap

    def event_whereami(self, event, area, lcords, gcords):
        print('event_whereami', area, lcords, gcords)
        self.lastcord = gcords
        if self.whereami_intercept:
            self.processmap(self.lastxmap, lcords, gcords)
            self.whereami_intercept = False
            return True, True

        