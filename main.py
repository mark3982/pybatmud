import socket
import sys

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtWebKit

class ConnectionDead(Exception):
    pass

class QProxy(QtGui.QFrame):
    def __init__(self, parent):
        super().__init__(parent)

    def mousePressEvent(self, event):
        pos = QtCore.QPoint(self.x() + event.x(), self.y() + event.y())
        event = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress, pos, event.button(), event.buttons(), QtCore.Qt.NoModifier)
        self.parent().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        self.parent().mouseReleaseEvent(event)
    def mouseMoveEvent(self, event):
        pos = QtCore.QPoint(self.x() + event.x(), self.y() + event.y())
        event = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, pos, event.button(), event.buttons(), QtCore.Qt.NoModifier)
        self.parent().mouseMoveEvent(event)

class QSubWindow(QtGui.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.moving = False
        self.sizing = False
        self.sizerproxy = QProxy(self)
        self.sizerproxy.resize(10, 10)
        self.sizerproxy.setStyleSheet('background-color: red;')
        self.sizerproxy.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def resizeEvent(self, event):
        self.sizerproxy.move(self.width() - 10, self.height() - 10)
        self.sizerproxy.raise_()

    def mousePressEvent(self, event):
        self.raise_()
        x = event.pos().x()
        y = event.pos().y()
        w = self.width()
        h = self.height()

        if x > w - 10 and y > h - 10:
            self.sizing = True
        else:
            self.moving = True
        self.oldx = self.x()
        self.oldy = self.y()
        self.oldpos = event.pos()
        self.oldw = self.width()
        self.oldh = self.height()

    def mouseReleaseEvent(self, event):
        self.moving = False
        self.sizing = False

    def mouseMoveEvent(self, event):
        if self.moving:
            posdelta = event.pos() - self.oldpos
            self.move(self.x() + posdelta.x(), self.y() + posdelta.y())
        if self.sizing:
            posdelta = event.pos() - self.oldpos
            self.resize(self.oldw + posdelta.x(), self.oldh + posdelta.y())


class Client:
    def __init__(self, host, port):
        self.inbuf = b''
        self.inlines = []
        self.connect()
        self.connected = False

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = True
        self.sock.connect((host, port))

    def readline(self, block = 0):
        # try to stay connected
        if not self.connected:
            raise ConnectionDead()

        if self.inbuf.find(b'\n') < 0:
            # no pending line so wait if needed
            self.sock.settimeout(block)
        else:
            # dont wait, we have a pending line
            self.sock.settimeout(0)
        try:
            data = self.sock.recv(4096)
            if not data:
                raise ConnectionDead()
            self.inbuf = self.inbuf + data
        except:
            pass

        # try to get line
        eols = self.inbuf.find(b'\n')
        if eols < 0:
            return None
        line = self.inbuf[0:eols].strip()
        self.inbuf = self.inbuf[eols + 1:]

        return line

    def writeline(self, line):
        if not self.connected:
            raise ConnectionDead()
        self.sock.send(line + b'\n')

class Priority:
    Monitor         =       100
    High            =       75
    Medium          =       50
    Normal          =       50
    Low             =       25

class Game:
    def __init__(self):
        self.c = Client('bat.org', 23)
        self.connected = False
        self.ereg = {}

    def activate(self):
        self.c.connect()
        # if successful then let all listeners
        # know that we have an established connection
        self.pushevent('connected')

    def registerforevent(self, event, cb, priority = Priority.Medium):
        """Register a callback to handle the event.
        """
        if event not in self.ereg:
            self.ereg[event] = []
        # insert into list with regard to priority
        cbs = self.ereg[event]
        x = 0
        for x in range(0, len(cbs) + 1):
            if x >= len(cbs):
                # append to end of list
                cbs.append((cb, priority))
                return
            if priority > cbs[x][1]:
                break
        cbs.insert(x, (cb, priority))

    def command(self, command):
        try:
            self.c.writeline(command)
        except ConnectionDead:
            if self.connected:
                # only raise event once until connection is
                # re-established
                self.connected = False
                self.pushevent('disconnected')
                # try to reconnect at least once
                self.activate()

    def tick(self, block = 10):
        while True:
            # read a single line
            try:
                line = self.c.readline(block = block)
            except ConnectionDead:
                if self.connected:
                    self.connected = False
                    self.pushevent('disconnected')
                    # try to reconnect at least once
                    self.activate()
            if line is None:
                break
            # push it as an unknown event first
            self.pushevent('unknown', line)

    def pushevent(self, event, *args):
        """Push the event to any registered callbacks.
        """
        print('event', event, args)
        if event not in self.ereg:
            return
        # call in priority ordering (highest first)
        for x in range(0, len(self.ereg[event])):
            cb = self.ereg[event][x]
            res = cb[0](event, *args)
            if res is True:
                # callback has specified to not forward
                # the event any further and we shall drop
                # it and not let it propagate
                return

class ProviderStandardEvent:
    """Provides standard events.

    This provides the standard events. Other extensions may create new
    events that enhance functionality or even push the same events. 
    This provides a base that all other extensions can be built with if
    desired. It may trap and discard some events and provide them in an
    enhanced form but generally this will be limited to unknown events or
    internally used events. 

    If a extension providers only events it is known as a Provider. If it
    simply adds functionlity it is known as a Plug, and if it provides both
    it shall also be known as a Plug hence the Provider prefix to this class.
    """
    def __init__(self, game):
        self.game = game
        # we are mainly concerned with translating unknown events into higher level events
        self.game.registerforevent('unknown', self.event_unknown, Priority.High)
        self.readbanner = True
        self.droploginopts = False
        self.banner = []

    def event_unknown(self, event, line):
        """Provides some standard higher level events.

        This is mainly going to take unknown events, which are the most basic
        and primitive event, and translate them into higher level events which
        reduces the code duplication that would be required by other extensions.

        It also reduces bugs and makes code more readable and compact by doing
        the most commonly needed things in this provider. If an extension is forced
        to interpret unknown events then it might be a good idea to put that code 
        here.
        """

        # we are done with login options
        if self.droploginopts and line.startswith(b'3 - '):
            self.droploginopts = False
            self.game.pushevent('login')
            return True

        if self.droploginopts:
            # just discard this crap
            return True

        # disable reading of banner and read up options
        if self.readbanner: 
            if line.startswith(b'1 - '):
                self.game.pushevent('banner', self.banner)
                self.readbanner = False
                self.droploginopts = True
                return True

        # let us grab the entire banner for safe keeping
        if self.readbanner:
            self.banner.append(line)
            return True

class QConsoleWindow(QSubWindow):
    """A Qt widget that provides a console like window.

    A Qt widget that provides a console like window with support for rendering
    terminal codes visually, and provides command input. This can be used to
    display select information such as game messages, channel messages, or even
    messages produced soley by the system.
    """
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.wp.resize(self.width() - 6, self.height() - 10 - 3)

    def __init__(self, pwin):
        super().__init__(pwin)
        self.pwin = pwin

        #self.mwin = self.pwin.getwin(xtype = QPlugUnkown)

        self.setStyleSheet('background-color: #444444; border-width: 1px; border-color: white; border-style: inset;')

        #self.sa = QtGui.QScrollArea(self.mwin)
        self.wp = QtWebKit.QWebView(self)
        self.wp.move(3, 10)
        self.wp.resize(600 - 6, 100 - 10 - 3)

        self.wp.setHtml('<html><body><span id="lines" style="color: white; line-height: 1; font-family: consolas;"></span></body></html>')

        self.wp.show()

        #self.wp.contentSizeChanged.connect(lambda: print('CHANGED'))

        #self.sa.setWidgetResizable(1)
        #self.sa.setWidget(self.wp)
        #self.sa.show()

        self.resize(600, 100)

        self.show()

    def processthenaddline(self, line):
        """Add line but convert terminal codes into HTML and convert from bytes to string.
        """
        # handle terminal codes
        parts = line.split(b'\x1b')

        line = []

        line.append(parts[0])

        for x in range(1, len(parts)):
            part = parts[x]
            cstr = part[0:part.find(b'm')]
            rmsg = part[part.find(b'm') + 1:]
            line.append(rmsg)

        line = b''.join(line)

        # now remove telnet escapes sequences because i
        # do not know what to do with them
        line = line.replace(b'\xff\xfc\x01', b'')

        parts = line.split(b'\xff')
        
        line = []
        line.append(parts[0])

        for x in range(1, len(parts)):
            part = parts[x]
            if part[0] == 0xff and part[1] == 0xfc:
                line.append(part[2:])
                continue
            line.append(part[1:])

        line = b''.join(line)

        # convert to string and replace any crazy characters
        line = line.decode('utf8', 'replace')

        self.addline(line)

    def addline(self, html):
        # add line to content with magic to make
        # it scroll ONLY if already scrolled near
        # to end of document (helps to lock it if
        # the user has it scrolled upwards when new
        # stuff is added)
        self.wp.page().mainFrame().evaluateJavaScript('var scrollit; if (document.body.scrollTop > document.body.scrollHeight - document.body.clientHeight - 1 || document.body.scrollTop == 0) scrollit = true; else scrollit = false; var m = document.createElement("div"); m.innerHTML = "%s"; lines.appendChild(m); if (scrollit) window.scrollTo(0, document.body.scrollHeight);' % html)

class QPlugUnknown(QConsoleWindow):
    """Provides debugging output.

    This widget is used to provide debugging and early testing output. It is not
    intended to be used in production or by normal end users under normal circumstances.
    If this provides production or normal functionality then that which it provides 
    should be moved to a another extension when possible.
    """
    def __init__(self, pwin, game):
        super().__init__(pwin)
        self.game = game

        self.resize(800, 500)

        game.registerforevent('banner', self.event_banner, Priority.Normal)
        game.registerforevent('unknown', self.event_unknown, Priority.Normal)

    def event_unknown(self, event, line):
        self.processthenaddline(line)

    def event_banner(self, event, lines):
        for line in lines:
            line = line.decode('utf8')
            line = line.replace(' ', '&nbsp;')
            self.addline(line)

class QPlugLogin:
    """Provides QT widget login window.

    This provides the login needed to enter into the game.
    """
    def __init__(self, pwin, game, xuser, xpass):
        super().__init__()
        self.xuser = xuser
        self.xpass = xpass
        self.pwin = pwin
        self.game = game

        # we only appear during the login sequence
        game.registerforevent('login', self.event_login)

        self.mwin = self.pwin.getwin()

        self.mwin.resize(200, 100)

        flo = QtGui.QFormLayout()
        self.mwin.setLayout(flo)

        self.leuser = QtGui.QLineEdit()
        self.lepass = QtGui.QLineEdit()
        self.btnlogin = QtGui.QPushButton()

        self.btnlogin.setText('Login')

        flo.addRow('User:', self.leuser)
        flo.addRow('Pass:', self.lepass)
        flo.addRow(self.btnlogin)

        self.btnlogin.clicked.connect(lambda: self.loginclicked())

    def loginclicked(self):
        if os.path.exists('dbglogin'):
            # development testing allows pulling from file
            fd = open('dbglogin', 'rb')
            data = fd.read()
            fd.close()

            parts = data.split(b':')
            xuser = parts[0]
            xpass = parts[1]
        else:
            # normal production code path pulls from form
            xuser = bytes(self.leuser.text(), 'utf8')
            xpass = bytes(self.lepass.text(), 'utf8')

        self.game.command(b'1')
        self.game.command(xuser)
        self.game.command(xpass)
        self.mwin.hide()

    def event_login(self, event):
        """Display the login window.
        """
        self.mwin.show()

class QMainWindow(QtGui.QWidget):
    def __init__(self):
        """Initialization
        """
        super().__init__()

        '''
        self.setWindowFlags(
            QtCore.Qt.CustomizeWindowHint | QtCore.Qt.Window | 
            QtCore.Qt.WindowCloseButtonHint
        )
        hlo = QtGui.QBoxLayout(0)
        self.netBytesIn = QtGui.QLabel()
        self.netBytesIn.setText('In')
        hlo.addWidget(self.netBytesIn)
        self.setLayout(hlo)
        '''

        self.setObjectName('MainWindow')
        self.setStyleSheet('background-color: black;')

        self.resize(850, 700)
        self.show()

        self.g = Game()
        self.stdep = ProviderStandardEvent(self.g)
        self.login = QPlugLogin(self, self.g, 'kmcg', 'k3ops9')
        self.unknown = QPlugUnknown(self, self.g)

        self.ticktimer = QtCore.QTimer(self)
        self.ticktimer.timeout.connect(lambda : self.gametick())
        self.ticktimer.start(50)

        self.setWindowTitle('Batmud Connection Information')

    def getwin(self, titlepad = 10):
        tframe = QSubWindow(self)
        tframe.setStyleSheet('background-color: #999999;')

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

    w = QMainWindow()

    sys.exit(app.exec_())

main()
