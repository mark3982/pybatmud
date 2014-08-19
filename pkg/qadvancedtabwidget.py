from PyQt4 import QtCore
from PyQt4 import QtGui

class TabState:
    Inactive        = 0
    Active          = 1
    Alerted         = 2

class QAdvancedTab:
    def __init__(self, tab, tablab):
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

class QAdvancedTabBar(QtGui.QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tabs = []
        self.clickcb = None
        self.lastActiveTab = None

        self.setObjectName('Test')

    def addTab(self, text):
        tab = QtGui.QWidget(self)
        tablab = QtGui.QLabel(tab)
        _tab = QAdvancedTab(tab, tablab)
        self.tabs.append(_tab)

        tablab.setText(text)
        tab.show()
        tablab.show()
        tablab.move(3, 3)

        tab.mousePressEvent = lambda event: self.tabMousePressEvent(_tab)

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
        wpe = self.width() / len(self.tabs)
        cx = 0
        for x in range(0, len(self.tabs)):
            tab = self.tabs[x]
            tab.tab.move(cx, 0)
            tab.tab.resize(wpe - 3, self.height() - 3)
            tab.tablab.resize(wpe, self.height())
            cx = cx + wpe

class QAdvancedTabWidget(QtGui.QFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.tabbar = QAdvancedTabBar(self)
        self.secwid = QtGui.QWidget(self)
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
        self.secwid.move(1, self.sectabheight)
        self.tabbar.move(1, 1)
        self.secwid.resize(self.width() - 2, self.height() - self.sectabheight - 2)
        self.tabbar.resize(self.width() - 2, self.sectabheight - 2)
        for g in self.tabs:
            g[1].resize(self.secwid.width(), self.secwid.height())

    def getTabParent(self):
        return self.secwid

    def addTab(self, widget, text):
        widget.setParent(self.secwid)
        # this hide call really does not seem to work
        widget.hide()
        # make sure active stays on top
        if self.lastActiveWidget is not None:
            self.lastActiveWidget.raise_()
        tab = self.tabbar.addTab(text)
        self.tabs.append((tab, widget))
        widget.resize(self.secwid.width(), self.secwid.height())
        #if self.lastActiveWidget is None:
        #    self.setCurrentWidget(widget)
