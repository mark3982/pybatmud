from PyQt4 import QtGui
from PyQt4 import QtCore

from pkg.qproxy import QProxy

class QSubWindow(QtGui.QFrame):
    def __init__(self, parent, title = None):
        super().__init__(parent)
        self.moving = False
        self.sizing = False
        self.sizerproxy = QProxy(self)
        self.sizerproxy.resize(10, 10)
        self.sizerproxy.setObjectName('SizerProxy')
        self.sizerproxy.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.sizerproxy.enterEvent = self.cursorEnterSizer
        self.sizerproxy.leaveEvent = self.cursorLeaveSizer

        self.title = title
        if title is not None:
            self.ltitle = QtGui.QLabel(self)
            self.ltitle.setObjectName('SubWindowTitle')
            self.ltitle.setText(title)
            self.ltitle.show()

            self.bmenu = QtGui.QPushButton(self)
            self.bmenu.setObjectName('SubWindowMenuButton')
            self.bmenu.resize(16, 16)
            self.bmenu.show()

            self.bmenu.move(2, 2)
            self.ltitle.move(20, 0)

        self.move(self.parent().width() * 0.5 - self.width() * 0.5, self.parent().height() * 0.5 - self.height() * 0.5)

    def resizeEvent(self, event):
        self.sizerproxy.move(self.width() - 10, self.height() - 10)
        self.sizerproxy.raise_()
        if self.title is not None:
            self.ltitle.resize(self.width() - 20, 20)

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

    def cursorLeaveSizer(self, event):
        self.setCursor(self.oldcursor)

    def cursorEnterSizer(self, event):
        self.oldcursor = self.cursor()
        self.setCursor(QtCore.Qt.SizeFDiagCursor)

    def mouseMoveEvent(self, event):
        if self.moving:
            posdelta = event.pos() - self.oldpos
            self.move(self.x() + posdelta.x(), self.y() + posdelta.y())
        if self.sizing:
            posdelta = event.pos() - self.oldpos
            self.resize(self.oldw + posdelta.x(), self.oldh + posdelta.y())
