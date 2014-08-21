"""Main startup for Qt4 and client initialization. 
"""
import socket
import sys
import os.path
import os
import sys

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtWebKit

from pkg.qproxy import QProxy
from pkg.qsubwindow import QSubWindow
from pkg.client import Client
from pkg.client import ConnectionDead
from pkg.game import Game
from pkg.game import Priority
from pkg.qconsolewindow import QConsoleWindow
from pkg.providerstandardevent import ProviderStandardEvent

from plug.qpluglogin import QPlugLogin
from plug.qplugunknown import QPlugUnknown
from plug.qplugcharacter import QPlugCharacter
from plug.qchannelmanager import QChannelManager
from plug.qplugspellman import QPlugSpellMan
from plug.qplugmodhealth import QPlugMobHealth

class QMainWindow(QtGui.QWidget):
    def __init__(self):
        """Initialization
        """
        super().__init__()

        # load the style sheet
        if sys.platform.find('win') == 0:
            fd = open('./styles/win_default.css', 'r')
            css = fd.read()
            fd.close()
        else:
            fd = open('./styles/default.css', 'r')
            css = fd.read()
            fd.close()

        self.setStyleSheet(css)

        self.setObjectName('MainWindow')

        path = os.path.expanduser('~') + '/pybatmud'
        if not os.path.exists(path):
            os.makedirs(path)

        self.resize(850, 700)
        self.show()

        # initialize the game, providers, and plugs - also order of
        # creation effects what windows are stacked on top or bottom
        self.g = Game()
        self.stdep = ProviderStandardEvent(self.g)
        #self.unknown = QPlugUnknown(self, self.g)
        self.character = QPlugCharacter(self, self.g)
        self.chanman = QChannelManager(self, self.g)
        self.login = QPlugLogin(self, self.g)
        self.spellman = QPlugSpellMan(self, self.g)
        self.mobhealth = QPlugMobHealth(self, self.g)
        self.g.start()

        self.ticktimer = QtCore.QTimer(self)
        self.ticktimer.timeout.connect(lambda : self.gametick())
        self.ticktimer.start(100)

        self.setWindowTitle('PyBatMud (Python Client For BatMud Using Qt) [kmcg3413@gmail.com]')

    def getwin(self, titlepad = 10):
        tframe = QSubWindow(self)

        tframe.setObjectName('TFrame')

        return tframe

    def gametick(self):
        """Allows the game instance to handle any tasks needed to be done.
        """
        self.g.tick(block = 0)

class QLocalApplication(QtGui.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.notifysuper = True

    def notify(self, receiver, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
            if isinstance(receiver, QConsoleWindow):
                receiver.keyPressEvent(event)                   # hand directly the QConsoleWindow
            if isinstance(receiver.parent(), QConsoleWindow):
                receiver.parent().keyPressEvent(event)          # hand to parent which is QConsoleWindow
            return True
        if self.notifysuper:
            return super().notify(receiver, event)
        return None

def main(standalone = False):
    if standalone:
        app = QLocalApplication(sys.argv)
        # Cleanlooks
        # Plastique
        # Motfif
        # CDE
        style = QtGui.QStyleFactory.create('Plastique')
        #app.setStyle(style)
        #app.setGraphicsSystem('raster')

    w = QMainWindow()

    if standalone:
        sys.exit(app.exec_())

'''
    What happens is if we are started directly just run as normal, but
    if the updater starts us then do nothing yet and let the updater
    tell us when to run. --kmcg
'''
if __name__ == '__main__':
    main(True)