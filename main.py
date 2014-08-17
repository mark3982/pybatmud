import socket
import sys
import os.path
import os

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

class QMainWindow(QtGui.QWidget):
    def __init__(self):
        """Initialization
        """
        super().__init__()

        # load the style sheet
        fd = open('./styles/default.css', 'r')
        css = fd.read()
        fd.close()

        self.setStyleSheet(css)


        self.setObjectName('MainWindow')

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

        self.ticktimer = QtCore.QTimer(self)
        self.ticktimer.timeout.connect(lambda : self.gametick())
        self.ticktimer.start(50)

        self.setWindowTitle('PyBatMud (Python Client For BatMud Using Qt) [kmcg3413@gmail.com]')

    def getwin(self, titlepad = 10):
        tframe = QSubWindow(self)

        tframe.setObjectName('TFrame')

        return tframe

    def gametick(self):
        """Allows the game instance to handle any tasks needed to be done.
        """
        self.g.tick(block = 0)

def main():
    app = QtGui.QApplication(sys.argv)
    # Cleanlooks
    # Plastique
    # Motfif
    # CDE
    style = QtGui.QStyleFactory.create('Plastique')
    app.setStyle(style)

    #app.setGraphicsSystem('raster')

    w = QMainWindow()

    sys.exit(app.exec_())

main()
