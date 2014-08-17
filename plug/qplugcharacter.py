"""The Qt widget module that will display player stats such as health, skill, endurance, and experience.
"""
from PyQt4 import QtGui
from PyQt4 import QtCore

from pkg.qsubwindow import QSubWindow

class QRisingLabel(QtGui.QLabel):
    def __init__(self, parent, text, stylename):
        super().__init__(parent)
        self.ticktimer = QtCore.QTimer(self)
        self.ticktimer.timeout.connect(lambda : self.tick())
        self.setObjectName(stylename)
        self.raise_()
        self.setText(text)
        self.show()
        self.ticktimer.start(100)
        self.move(self.parent().width(), self.parent().height())
    def tick(self):
        if self.y() - 1 < 0:
            # delete myself, hopefully...
            self.ticktimer.stop()
            self.setParent(None)
            return 

        pft = (self.parent().height() - self.y()) / self.parent().height()

        mv = 5 + pft * 40

        self.move(self.parent().width() - self.width() - 5, self.y() - mv)

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
                rl = QRisingLabel(self.parent(), '%s' % hpd, 'RisingLabelPointsEntityHealth')            

        self.elast = hp

    def event_stats(self, event, hp, sp, ep, ex):
        print('stats', hp, sp, ep, ex)
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

            print('hpd:%s spd:%s epd:%s exd:%s' % (hpd, spd, epd, exd))
            print(hp, sp, ep, ex)
            print(self.last)

            if hpd != 0:
                rl = QRisingLabel(self.parent(), '%s' % hpd, 'RisingLabelPointsHealth')
            if spd != 0:
                rl = QRisingLabel(self.parent(), '%s' % spd, 'RisingLabelPointsSpirit')
            if epd != 0:
                rl = QRisingLabel(self.parent(), '%s' % epd, 'RisingLabelPointsEndurance')
            if exd != 0:
                rl = QRisingLabel(self.parent(), '%s' % exd, 'RisingLabelPointsExperience')
        self.last = (hp, sp, ep, ex)

