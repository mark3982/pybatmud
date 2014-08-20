import os

from PyQt4 import QtGui
from pkg.qsubwindow import QSubWindow

class QPlugLogin(QSubWindow):
    """Provides QT widget login window.

    This provides the login needed to enter into the game.
    """
    def __init__(self, pwin, game):
        super().__init__(pwin)
        self.pwin = pwin
        self.game = game

        # we only appear during the login sequence
        game.registerforevent('login', self.event_login)

        self.setObjectName('QPlugLogin')

        self.resize(200, 100)

        flo = QtGui.QFormLayout()
        self.setLayout(flo)

        self.leuser = QtGui.QLineEdit()
        self.lepass = QtGui.QLineEdit()
        self.btnlogin = QtGui.QPushButton()

        self.btnlogin.setText('Login')

        flo.addRow('User:', self.leuser)
        flo.addRow('Pass:', self.lepass)
        flo.addRow(self.btnlogin)

        self.btnlogin.clicked.connect(lambda: self.loginclicked())

        if os.path.exists('dbglogin'):
            print('loading user/pass from disk')
            fd = open('dbglogin', 'r')
            data = fd.read()
            fd.close()

            parts = data.split(':')
            xuser = parts[0]
            xpass = parts[1]
            self.leuser.setText(xuser)
            self.lepass.setText(xpass)

    def loginclicked(self):
        # normal production code path pulls from form
        xuser = bytes(self.leuser.text(), 'utf8')
        xpass = bytes(self.lepass.text(), 'utf8')

        if len(xuser) < 1 or len(xpass) < 1:
            QtGui.QMessageBox.warning(self, 'Login', 'The user and password fields must be filled out.')
            return


        self.game.command(xuser)
        self.game.command(xpass)
        self.hide()

    def event_login(self, event):
        """Display the login window.
        """
        self.show()