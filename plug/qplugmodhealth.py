import time

from PyQt4 import QtGui
from PyQt4 import QtCore

from pkg.qsubwindow import QSubWindow
from pkg.dprint import dprint

class QPlugMobHealth(QSubWindow):
    def __init__(self, pwin, game):
        super().__init__(pwin)
        self.game = game

        self.bar = QtGui.QFrame(self)
        self.txt = QtGui.QLabel(self)

        self.move(400, 0)
        self.resize(400, 30)

        self.txt.setAlignment(QtCore.Qt.AlignCenter)

        self.setStyleSheet(self.parent().styleSheet())

        self.bar.setObjectName('MobHealthBar')
        self.txt.setObjectName('MobHealthBarText')

        self.bar.resize(0, self.height())
        self.txt.resize(self.width(), self.height())
        self.txt.setText('Mob Health')

        self.bar.show()
        self.txt.show()
        self.show()

        game.registerforevent('mobhealth', self.event_mobhealth)

    def resizeEvent(self, event):
        self.bar.resize(self.bar.width(), self.height())
        self.txt.resize(self.width(), self.height())
        self.txt.raise_()

    def event_mobhealth(self, event, name, health):
        print('modhealth', health)

        p = health / 100
        p = self.width() * p

        self.bar.resize(p, self.height())
        if p == 0:
            self.txt.setText('Mob Health View')
        else:
            self.txt.setText('%s (%s)' % (name, health))



