"""The Qt widget module that will display player stats such as health, skill, endurance, and experience.
"""
import random

from PyQt4 import QtGui
from PyQt4 import QtCore

from pkg.qsubwindow import QSubWindow

class QRisingLabel(QtGui.QLabel):
    list = []
    all = []

    def __init__(self, parent, text, stylename, posoff):
        super().__init__(parent)
        self.setObjectName(stylename)
        self.raise_()
        self.setText(text)
        self.show()
        self.posoff = posoff
        self.move(self.parent().width(), self.parent().height())
        for w in QRisingLabel.list:
            w.move(self.x(), self.y() - self.height())
        QRisingLabel.list.append(self)
        QRisingLabel.all.append(self)

    def tick():
        for w in QRisingLabel.all:
            w._tick()

    def _tick(self):
        if self in QRisingLabel.list:
            QRisingLabel.list.remove(self)

        if self.y() - 1 < 0:
            # delete myself, hopefully...s
            self.hide()
            self.setParent(None)
            self.all.remove(self)
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
        self.text.move(0, 0)
        self.text.setAlignment(QtCore.Qt.AlignCenter)
        self.update()

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
        self.text.resize(self.width(), self.height())


class QPlugCharacter(QSubWindow):
    def __init__(self, pwin, game):
        super().__init__(pwin)
        self.myclass = None

        game.registerforevent('stats', self.event_stats)
        game.registerforevent('riftentitystats', self.event_riftentitystats)
        game.registerforevent('playerstatus', self.event_playerstatus)

        self.ticktimer = QtCore.QTimer(self)
        self.ticktimer.timeout.connect(self.tick)
        self.ticktimer.start(100)

        self.move(0, 0)

        self.resizeon(False)

        self.sbhp = QStatBar(self, 'HP', 'StatsHealth')
        self.sbsp = QStatBar(self, 'SP', 'StatsSpirit')
        self.sbep = QStatBar(self, 'EP', 'StatsEndurance')
        self.sbeh = QStatBar(self, 'EHP', 'StatsEntityHealth')
        self.classimage = QtGui.QLabel(self)

        h = 15
        wo = 60

        self.resize(400, h * 4)

        self.sbhp.move(wo, h * 0)
        self.sbhp.resize(self.width() - wo, h)
        self.sbsp.move(wo, h * 1)
        self.sbsp.resize(self.width() - wo, h)
        self.sbep.move(wo, h * 2)
        self.sbep.resize(self.width() - wo, h)
        self.sbeh.move(wo, h * 3)
        self.sbeh.resize(self.width() - wo, h)

        for w in (self.sbhp, self.sbsp, self.sbep, self.sbeh):
            w.setmax(1)
            w.setval(0)

        self.classimage.resize(wo, self.height())

        self.last = None
        self.elast = None

        self.show()

    def event_playerstatus(self, event, who, xclass, level):
        if who != '$me':
            return

        if self.myclass != xclass:
            print('SETTING PIC')
            self.myclass = xclass
            # update our character portrait
            self.classimage.setPixmap(QtGui.QPixmap('./media/classpics/%s_%s.png' % (xclass, 'male')))

    def tick(self):
        QRisingLabel.tick()

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

        if self.last is None:
            self.sbeh.setmax(1)
            self.sbeh.setval(0)

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

