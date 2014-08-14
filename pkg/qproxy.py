from PyQt4 import QtGui
from PyQt4 import QtCore

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
