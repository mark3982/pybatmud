import math

from PyQt4 import QtCore
from PyQt4 import QtGui

class TabState:
    Inactive        = 0
    Active          = 1
    Alerted         = 2

class QAdvancedTab:
    def __init__(self, tab, tablab, tabbar):
        self.tabbar = tabbar
        self.tab = tab
        self.tablab = tablab
        self.tablab.setObjectName('TabLabel')
        self.tablab.setAlignment(QtCore.Qt.AlignCenter)
        self.setState(TabState.Inactive)

    def setState(self, value):
        if value == TabState.Active:
            self.tab.setObjectName('TabActive')
        elif value == TabState.Inactive:
            self.tab.setObjectName('TabInactive')
        else:
            self.tab.setObjectName('TabAlerted')
        self.tab.style().unpolish(self.tab)
        self.tab.style().polish(self.tab)

    def remove(self):
        self.tabbar.remTab(self)

class QAdvancedTabBar(QtGui.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tabs = []
        self.clickcb = None
        self.lastActiveTab = None

        self.setObjectName('Test')

    def remTab(self, tab):
        self.tabs.remove(tab)
        tab.tab.hide()
        tab.tab.setParent(None)
        tab.tablab.hide()
        tab.tablab.setParent(None)
        self.arrange()

    def addTab(self, text, menu = None):
        tab = QtGui.QWidget(self)
        tablab = QtGui.QLabel(tab)
        _tab = QAdvancedTab(tab, tablab, self)
        self.tabs.append(_tab)

        tablab.setText(text)
        tab.show()
        tablab.show()
        tablab.move(0, 0)

        tab.mousePressEvent = lambda event: self.tabMousePressEvent(_tab)
        if menu is not None:
            tablab.contextMenuEvent = lambda event: menu.exec(event.globalPos())

        _tab.setState(TabState.Inactive)

        self.arrange()
        return _tab

    def tabMousePressEvent(self, tab):
        if self.lastActiveTab is not None:
            self.lastActiveTab.setState(TabState.Inactive)
        tab.setState(TabState.Active)
        self.lastActiveTab = tab
        self.clickcb(tab)

    def setTabActive(self, tab):
        self.tabMousePressEvent(tab)

    def setClickedCallback(self, cb):
        self.clickcb = cb

    def resizeEvent(self, event):
        self.arrange()

    def arrange(self):
        if len(self.tabs) < 1:
            return
        rowcnt = math.ceil(len(self.tabs) / 8)
        wpe = self.width() / min(8, len(self.tabs))
        hpe = self.height() / rowcnt

        cx = 0
        cy = 0
        for x in range(0, len(self.tabs)):
            tab = self.tabs[x]
            tab.tab.move(cx + 1, cy + 1)
            tab.tab.resize(wpe - 3, hpe - 3)
            tab.tablab.resize(wpe - 3, hpe - 3)
            cx = cx + wpe
            if x % 8 == 7:
                cx = 0
                cy = cy + hpe

class QAdvancedTabWidget(QtGui.QFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.split = QtGui.QSplitter(self)
        self.tabbar = QAdvancedTabBar(self)
        self.secwid = QtGui.QFrame(self)

        self.secwid.resizeEvent = lambda event: self.secwidresize(self.secwid, event)

        self.split.setOrientation(0)
        self.split.addWidget(self.tabbar)
        self.split.addWidget(self.secwid)
        self.split.setSizes([50, 500])

        self.split.show()

        self.sectabheight = 40
        self.tabs = []

        self.tabbar.show()
        self.secwid.show()

        self.setObjectName('TabWidgetArea')

        self.tabbar.setClickedCallback(self.tabClickedEvent)

        self.lastActiveWidget = None

    def tabClickedEvent(self, tab):
        for g in self.tabs:
            if g[0] is tab:
                if self.lastActiveWidget is not None:
                    self.lastActiveWidget.hide()
                g[1].show()
                g[1].raise_()
                self.lastActiveWidget = g[1]

    def count(self):
        return len(self.tabs)

    def widget(self, i):
        return self.tabs[i][1]

    def tab(self, widget):
        for g in self.tabs:
            if g[1] is widget:
                return g[0]

    def setMovable(self, value):
        pass

    def setCurrentWidget(self, widget):
        for g in self.tabs:
            if g[1] is widget:
                self.tabbar.setTabActive(g[0])
                self.tabClickedEvent(g[0])
                return

    def currentWidget(self):
        return self.lastActiveWidget

    def resizeEvent(self, event):
        #self.secwid.move(1, self.sectabheight)
        #self.tabbar.move(1, 1)
        #self.secwid.resize(self.width() - 2, self.height() - self.sectabheight - 2)
        #self.tabbar.resize(self.width() - 2, self.sectabheight - 2)
        self.split.resize(self.width(), self.height())
        #self.secwid.resize(self.secwid.parent().width(), self.secwid.parent().height())

    def secwidresize(self, secwid, event):
        for g in self.tabs:
            g[1].resize(secwid.width(), secwid.height())

    def getTabParent(self):
        return self.secwid

    def removeWidget(self, w):
        for i in self.tabs:
            if i[1] is w:
                break
        self.tabs.remove(i)
        i[0].remove()
        i[1].hide()
        i[1].setParent(None)

    def addTab(self, widget, text, menu = None):
        widget.setParent(self.secwid)
        # this hide call really does not seem to work
        widget.hide()
        # make sure active stays on top
        if self.lastActiveWidget is not None:
            self.lastActiveWidget.raise_()
        tab = self.tabbar.addTab(text, menu)
        self.tabs.append((tab, widget))
        widget.resize(self.secwid.width(), self.secwid.height())
        #if self.lastActiveWidget is None:
        #    self.setCurrentWidget(widget)
