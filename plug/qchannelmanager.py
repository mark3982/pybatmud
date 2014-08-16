from PyQt4 import QtGui

from pkg.qsubwindow import QSubWindow
from pkg.game import Priority
from pkg.qconsolewindow import QConsoleWindow

class QChannelManager:
    def __init__(self, parent, game):
        self.game = game
        self.parent = parent

        self.chistoryndx = -1
        self.chistory = ['']
        self.holdchangeupdated = False

        # create initial channel group
        self.chgrpwidgets = []

        # default channels created (maybe need to try to load from disk here!)
        self.createchannelgroup({
            'All':      ('$all',),        # first tab channels named All
            'Tells':    ('$tells',),
            'Sales':    ('#sales',),
            'Sky-':     ('#sky',),
            'Newbie':   ('#newbie',)
        })

        game.registerforevent('prompt', self.event_prompt, Priority.Normal)
        game.registerforevent('banner', self.event_banner, Priority.Normal)
        game.registerforevent('unknown', self.event_unknown, Priority.Normal)
        game.registerforevent('channelmessage', self.event_channelmessage, Priority.Normal)

    def event_channelmessage(self, event, chan, who, msg, line):
        print('channel message', chan, who, msg)
        chan = ('#%s' % chan).lower()
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                page = tabctrl.widget(i)
                chanlist = page.chanlist
                if chan in chanlist:
                    print('    sent to page')
                    page.processthenaddline(line)
    def event_prompt(self, event, prompt):
        # send prompt to ALL consoles
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                page = tabctrl.widget(i)
                page.setprompt(prompt)
    def event_banner(self, event, banner):
        pass
    def event_unknown(self, event, line):
        """Route the message to the appropriate page in tab control.
        """
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            # go through pages on tab control
            for i in range(0, tabctrl.count()):
                page = tabctrl.widget(i)
                chanlist = page.chanlist
                if '$all' in chanlist:
                    page.processthenaddline(line)

    def commandEvent(self, line):
        # set history line
        self.chistory[-1] = line
        # make new history line
        self.chistory.append('')
        self.game.command(line)

    def updowncallback(self, up):
        """When up or down arrow keys are used on any managed QConsoleWindow.
        """
        if not up and self.chistoryndx == -1:
            # do not do anything.. we are at bottom already
            return
        if up and -self.chistoryndx == len(self.chistory):
            # we are already at top.. nothing we can do
            return
        if up:
            self.chistoryndx -= 1
        if not up:
            self.chistoryndx += 1
        # update command boxes
        print('self', self)
        print('self.chistoryndx:%s self.chistory:%s' % (self.chistoryndx, self.chistory))
        self.holdchangeupdated = True
        self.setallcommandinputsto(self.chistory[self.chistoryndx])
        self.holdchangeupdated = False

    def setallcommandinputsto(self, text):
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                page = tabctrl.widget(i)
                page.setcommandline(text)

    def commandchangedcallback(self, text):
        """When command input changes on any mananged QConsoleWindow.
        """
        if self.holdchangeupdated:
            return
        # reset index to end of history for command being newly typed
        self.chistoryndx = -1
        # propagate the change across all command inputs and
        # enter it into the current history line
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                page = tabctrl.widget(i)
                page.setcommandline(text)
        self.chistory[-1] = text
        print('update history with', text, self.chistory)

    def createchannelgroup(self, channelgroups = {}):
        """Creates new channel group window.
        """
        css = self.parent.styleSheet()
        chgrpwidget = QSubWindow(self.parent, 'Channel Window')
        chgrpwidget.setStyleSheet(css)
        chgrpwidget.resize(600, 400)
        clientarea = chgrpwidget.getclientarea()
        qtabwidget = QtGui.QTabWidget(clientarea)
        def __resizeEvent(event):
            qtabwidget.resize(clientarea.width(), clientarea.height())
        clientarea.resizeEvent = __resizeEvent
        # make console widgets
        css = self.parent.styleSheet()
        for changrptitle in channelgroups:
            channels = channelgroups[changrptitle]
            qconsole = QConsoleWindow(None, css)
            # we want notification when the command line changes on any window
            qconsole.setupdowncallback(self.updowncallback)
            qconsole.setcommandchangedcallback(self.commandchangedcallback)
            qtabwidget.addTab(qconsole, ', '.join(channels))
            qconsole.chanlist = channels
            qconsole.commandEvent = self.commandEvent
            qconsole.show()
        # save the sub-window and tab widget
        self.chgrpwidgets.append([chgrpwidget, qtabwidget, channels])
        chgrpwidget.show()
        qtabwidget.show()


