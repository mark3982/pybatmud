"""The Qt widget module that will display player stats such as health, skill, endurance, and experience.
"""
import random

from PyQt4 import QtGui
from PyQt4 import QtCore

from pkg.qsubwindow import QSubWindow

class QRisingLabel(QtGui.QLabel):
    list = []

    def __init__(self, parent, text, stylename, posoff):
        super().__init__(parent)
        self.ticktimer = QtCore.QTimer(self.parent())
        ticktimer = self.ticktimer

        def __tick():
            try:
                self.tick()
            except Exception as e:
                print(e)
                ticktimer.stop()

        self.ticktimer.timeout.connect(__tick)
        self.setObjectName(stylename)
        self.raise_()
        self.setText(text)
        self.show()
        self.posoff = posoff
        self.move(self.parent().width(), self.parent().height())
        for w in QRisingLabel.list:
            w.move(self.x(), self.y() - self.height())
        QRisingLabel.list.append(self)
        self.ticktimer.start(100)

    def tick(self):
        if self in QRisingLabel.list:
            QRisingLabel.list.remove(self)

        if self.y() - 1 < 0:
            # delete myself, hopefully...
            self.ticktimer.stop()
            self.setParent(None)
            return 

        pft = (self.parent().height() - self.y()) / self.parent().height()
        mv = 5 + pft * 40

        self.move((self.parent().width() - self.width() - 5) + self.posoff[0], (self.y() - mv) + self.posoff[1])

class QStatBar(QtGui.QFrame):
    def __init__(self, parent, tprefix, stylename):
        super().__init__(parent)
        self.xmax = 1.0
        self.xvalue = 0.0
        self.setObjectName(stylename)
        self.wleft = QtGui.QFrame(self)
        self.wright = QtGui.QFrame(self)
        self.text = QtGui.QLabel(self)
        self.wleft.setObjectName('StatBarLeft')
        self.wright.setObjectName('StatBarRight')
        self.tprefix = tprefix
        self.text.resize(self.width(), self.height())
        self.update()
        self.text.move(self.width() * 0.5, 0)

    def settextprefix(self, text):
        self.tprefix = text

    def setmax(self, xmax):
        self.xmax = xmax
        self.update()

    def setval(self, xvalue):
        self.xvalue = xvalue
        self.update()

    def update(self):
        val = self.xvalue / self.xmax
        lw = val * self.width()
        rw = self.width() - lw
        self.wleft.resize(lw, self.height())
        self.wright.move(lw, 0)
        self.wright.resize(rw, self.height())
        self.text.setText('%s %s/%s' % (self.tprefix, self.xvalue, self.xmax))        


class QPlugCharacter(QSubWindow):
    def __init__(self, pwin, game):
        super().__init__(pwin)
        game.registerforevent('stats', self.event_stats)
        game.registerforevent('riftentitystats', self.event_riftentitystats)

        self.move(0, 0)

        self.resizeon(False)

        self.sbhp = QStatBar(self, 'HP', 'StatsHealth')
        self.sbsp = QStatBar(self, 'SP', 'StatsSpirit')
        self.sbep = QStatBar(self, 'EP', 'StatsEndurance')
        self.sbeh = QStatBar(self, 'EHP', 'StatsEntityHealth')

        h = 33

        self.resize(400, h * 4)

        self.sbhp.move(0, h * 0)
        self.sbhp.resize(self.width(), h)
        self.sbsp.move(0, h * 1)
        self.sbsp.resize(self.width(), h)
        self.sbep.move(0, h * 2)
        self.sbep.resize(self.width(), h)
        self.sbeh.move(0, h * 3)
        self.sbeh.resize(self.width(), h)

        self.last = None
        self.elast = None

        self.show()

    def event_riftentitystats(self, event, ename, hp):
        self.sbeh.setmax(hp[1])
        self.sbeh.setval(hp[0])

        if self.elast is not None:
            hpd = hp[0] - self.elast[0]
            if hpd != 0:
                posoff = (-random.randint(0, 20), 0)
                rl = QRisingLabel(self.parent(), '%s' % hpd, 'RisingLabelPointsEntityHealth', posoff) 

        self.elast = hp

    def event_stats(self, event, hp, sp, ep, ex):
        self.sbhp.setmax(hp[1])
        self.sbhp.setval(hp[0])
        self.sbsp.setmax(sp[1])
        self.sbsp.setval(sp[0])
        self.sbep.setmax(ep[1])
        self.sbep.setval(ep[0])

        if self.last is not None:
            # see what changed and display on screen in an interesting way
            hpd = hp[0] - self.last[0][0]
            spd = sp[0] - self.last[1][0]
            epd = ep[0] - self.last[2][0]
            exd = ex - self.last[3]

            if hpd != 0:
                posoff = (-random.randint(0, 20), 0)
                rl = QRisingLabel(self.parent(), '%+d' % hpd, 'RisingLabelPointsHealth', posoff)
            if spd != 0:
                posoff = (-random.randint(0, 20), 0)
                rl = QRisingLabel(self.parent(), '%+d' % spd, 'RisingLabelPointsSpirit', posoff)
            if epd != 0:
                posoff = (-random.randint(0, 20), 0)
                rl = QRisingLabel(self.parent(), '%+d' % epd, 'RisingLabelPointsEndurance', posoff)
            if exd != 0:
                posoff = (-random.randint(0, 20), 0)
                rl = QRisingLabel(self.parent(), '%+d' % exd, 'RisingLabelPointsExperience', posoff)
        self.last = (hp, sp, ep, ex)

