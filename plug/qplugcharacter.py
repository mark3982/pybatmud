"""The Qt widget module that will display player stats such as health, skill, endurance, and experience.
"""
from PyQt4 import QtGui

from pkg.qsubwindow import QSubWindow

class QStatBar(QtGui.QFrame):
    def __init__(self, parent, tprefix):
        super().__init__(parent)
        self.xmax = 1.0
        self.xvalue = 0.0
        self.wleft = QtGui.QFrame(self)
        self.wright = QtGui.QFrame(self)
        self.text = QtGui.QLabel(self)
        self.wleft.setObjectName('StatBarLeft')
        self.wright.setObjectName('StatBarRight')
        self.tprefix = tprefix
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
        self.wright.resize(rw, self.height())
        self.text.setText('%s %s/%s' % (self.tprefix, self.xvalue, self.xmax))


class QPlugCharacter(QSubWindow):
    def __init__(self, pwin, game):
        super().__init__(pwin)
        game.registerforevent('stats', self.event_stats)

        self.resize(400, 100)

        self.sbhp = QStatBar(self, 'HP')
        self.sbsp = QStatBar(self, 'SP')
        self.sbep = QStatBar(self, 'EP')

        self.sbhp.move(0, 0)
        self.sbhp.resize(400, 33)
        self.sbsp.move(0, 33)
        self.sbsp.resize(400, 33)
        self.sbep.move(0, 66)
        self.sbep.resize(400, 33)

        self.show()

    def event_stats(self, event, hp, sp, ep, ex):
        print('stats', hp, sp, ep, ex)
        self.sbhp.setmax(hp[1])
        self.sbhp.setval(hp[0])
        self.sbsp.setmax(sp[1])
        self.sbsp.setval(sp[0])
        self.sbep.setmax(ep[1])
        self.sbep.setval(ep[0])

