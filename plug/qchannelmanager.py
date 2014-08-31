"""Contains channel group management.

This entire module contains a single object called QChannelManager which provides
complete control over one or more channel windows where each window has one or more
channels and each channel has one or more inputs. The channel in the channel window
are represented by tabs.

    * provides command history
    * synchronizes command inputs across all consoles
    * routes messages to appropriate windows

Author: LK McGuire (kmcg3413@gmail.com)
"""
import os.path
import random
import math
import datetime

from PyQt4 import QtCore
from PyQt4 import QtGui

from pkg.qsubwindow import QSubWindow
from pkg.game import Priority
from pkg.qconsolewindow import QConsoleWindow
from pkg.qadvancedtabwidget import QAdvancedTabWidget
from pkg.qadvancedtabwidget import TabState
from pkg.dprint import dprint

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
        self.mainchgrpwidget = self.createchannelgroup({
            'All':      ('$all',),        # first tab channel named All
            'Battle':   ('$battle',),
            'Readme':   ('$readme',),
        })

        game.registerforevent('prompt', self.event_prompt, Priority.Normal)
        game.registerforevent('banner', self.event_banner, Priority.Normal)
        game.registerforevent('lineunknown', self.event_lineunknown, Priority.Normal)
        game.registerforevent('channelmessage', self.event_channelmessage, Priority.Normal)
        game.registerforevent('tell', self.event_tell, Priority.Normal)
        game.registerforevent('battlemessage', self.event_battlemessage, Priority.Normal)

        self.pcolor = self.loadpcolor()

    def savepcolor(self):
        fd = open('pcolor', 'w')
        fd.write('%s' % self.pcolor)
        fd.close()

    def pcolortupletohex(self, t):
        return '%02x%02x%02x' 

    def makepcolorfor(self, name):
        r = random.randint(60, 255)
        g = random.randint(60, 255)
        b = random.randint(60, 255)
        self.pcolor[name] = (r, g, b)

    def getpcolorfor(self, name):
        if name not in self.pcolor:
            self.makepcolorfor(name)
            # likely could be inefficient with a LOT of
            # names, but will address that issue when the
            # time comes for now lets employ KISS
            self.savepcolor()

        return '%02x%02x%02x' % (self.pcolor[name][0], self.pcolor[name][1], self.pcolor[name][2])

    def loadpcolor(self):
        if os.path.exists('pcolor'):
            fd = open('pcolor', 'r')
            pcolor = eval(fd.read())
            fd.close()
            return pcolor
        return {}

    def event_battlemessage(self, event, line):
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                console = tabctrl.widget(i)
                chanlist = console.chanlist
                if '$battle' in chanlist:
                    self.addlinetoconsole(console, line)

    def event_channelmessage(self, event, chan, who, msg, line):
        added = False
        chan = ('#' + chan).lower()

        pcolor = self.getpcolorfor(who)
        now = datetime.datetime.now()
        now = now.strftime('%m:%d:%H:%M')
        fmsg = bytes('[%s] \x1b#%sm%s\x1bm: %s' % (now, pcolor, who.ljust(10), msg), 'utf8')

        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                console = tabctrl.widget(i)
                chanlist = console.chanlist
                if chan in chanlist:
                    self.addlinetoconsole(console, fmsg)
                    added = True
        if not added:
            # automatically create a channel to hold conversation
            console = self.createchannel(self.mainchgrpwidget, (chan,), chan)
            self.addlinetoconsole(console, fmsg)

    def event_prompt(self, event, prompt):
        """Set the prompt on all managed consoles.
        """
        # send prompt to ALL consoles
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                page = tabctrl.widget(i)
                page.setprompt(prompt)
    def event_banner(self, event, banner):
        """Routes the banner through the unknown event handler.
        """
        for item in banner:
            self.event_lineunknown(event, item)
    def event_tell(self, event, fromwho, towho, line):
        """Route tell to appropriate channel.

        We route the tell to the appropriate channel by first looking
        for a channel that will accept it. We also route it to any 
        channel that has a $tell input. If we do not find a channel
        that accepts it without using the $tell input then we create
        a new channel with that input only.
        """

        # swap if from ourselves
        if fromwho == '$me':
            fromwho = towho
        fromwho = '!' + fromwho
        delivered = False
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                console = tabctrl.widget(i)
                if fromwho in console.chanlist:
                    self.addlinetoconsole(console, line)
                    delivered = True
                if '$tells' in console.chanlist:
                    # special channel mostly from pre-development work, but
                    # i am keeping around just because im not ready to remove
                    # it yet
                    self.addlinetoconsole(console, line)
        if delivered is False:
            # ok we did not find a window to handle this.. so we need
            # to create a channel in a window that can handle it
            console = self.createchannel(self.mainchgrpwidget, (fromwho,), fromwho)
            self.addlinetoconsole(console, line)

    def event_lineunknown(self, event, line):
        """Route the message to the appropriate page in tab control.

        A unknown message is one that has not or can not be catagorized
        into a more specific event. It could be very important so we 
        ensure that it is at least routed to the $all input. I suspect
        most players will keep an eye on their $all channel to make sure
        they are not missing anything important as it serves as a overall
        view of everything that is going on.
        """
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            # go through pages on tab control
            for i in range(0, tabctrl.count()):
                console = tabctrl.widget(i)
                chanlist = console.chanlist
                if '$all' in chanlist:
                    self.addlinetoconsole(console, line)

    def addlinetoconsole(self, console, line):
        tabwidget = console.parent().parent().parent()

        # would have used an `is` but some python implementations
        # may not handle it correctly so to be safe i use the `==`
        # -kmcg
        if tabwidget.currentWidget() != console:
            tabwidget.tab(console).setState(TabState.Alerted)

        console.processthenaddline(line)

    def commandEvent(self, line):
        """When the command input on any channel window changes.
        """
        # set history line, only if not a movement command
        if line not in {'n', 's', 'w', 'e', 'nw', 'ne', 'sw', 'se'}:
            self.chistory[-1] = line
            # make new history line
            self.chistory.append('')
        res = self.game.pushevent('command', line)
        if res is True or (type(res) == tuple and res[0] is True):
            dprint('dropped command')
            # the command was intercepted, processed, and the handler
            # has requested that we drop the command and not forward
            # it to the game
            return
        self.game.command(line)

    def updowncallback(self, up):
        """When up or down arrow keys are used.
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
        self.holdchangeupdated = True
        self.setallcommandinputsto(self.chistory[self.chistoryndx])
        self.holdchangeupdated = False

    def setallcommandinputsto(self, text):
        """Set all command inputs to this value.
        """
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                page = tabctrl.widget(i)
                page.setcommandline(text)

    def commandchangedcallback(self, text):
        """When command input changes on any mananged console.
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
                # little fix here, if it has focus and we do this once they
                # type a character we will throw the edit position back to
                # the end of the line which is VERY annoying
                if not page.ce.hasFocus():
                    page.setcommandline(text)
        self.chistory[-1] = text

    def createchannel(self, chgrpwidget, channels, title):
        """Create channel in specified channel group.
        """
        tabwidget = chgrpwidget.qtabwidget
        css = self.parent.styleSheet()
        qconsole = QConsoleWindow(tabwidget.getTabParent(), css)
        qconsole.hide()
        qconsole.setupdowncallback(self.updowncallback)
        qconsole.setcommandchangedcallback(self.commandchangedcallback)

        def __close():
            tabwidget.removeWidget(qconsole)

        menu = QtGui.QMenu(self.parent)
        if '$all' not in channels and '$battle' not in channels:
            a1 = QtGui.QAction('Close', self.parent)
            a1.triggered.connect(__close)
            menu.addAction(a1)

        tabwidget.addTab(qconsole, title, menu)
        qconsole.show()

        qconsole.chanlist = channels

        # check if single input
        if len(channels) < 2:
            # check if channel only
            if channels[0][0] == '#':
                builtin = (
                    'bat', 'bs', 'd3', 'ghost', 'ifin', 'lfp',
                    'newbie', 'race', 'suomi', 'battlebot',
                    'chat', 'eso', 'hockey', 'imud', 'magical',
                    'sports', 'tunes', 'boardgaming', 'client',
                    'football', 'houses', 'infalert', 'mudcon',
                    'politics', 'sales', 'stream', 'wanted'
                )
                # this actually became annoying..
                #if channels[0][1:] in builtin:
                #    qconsole.setcommandprefix('%s ' % (channels[0][1:]))
                #else:
                #    qconsole.setcommandprefix('%s say ' % (channels[0][1:]))
            if channels[0][0] == '!':
                # add prefix for talking over tells to player
                qconsole.setcommandprefix('tell %s ' % (channels[0][1:]))
            if channels[0] == '$readme':
                if os.path.exists('README'):
                    readme = 'README'
                if os.path.exists('./client/README'):
                    readme = './client/README'
                fd = open(readme, 'r')
                dprint('readme', 'rb')
                lines = fd.readlines()
                for line in lines:
                    line = bytes(line, 'utf8').strip(b'\r\n').replace(b'\\x1b', b'\x1b')
                    self.addlinetoconsole(qconsole, line)
                fd.close()

        qconsole.commandEvent = self.commandEvent
        qconsole.show()
        return qconsole

    def createchannelgroup(self, channelgroups = {}):
        """Create a new channel group window.
        """
        allconsole = None
        css = self.parent.styleSheet()
        chgrpwidget = QSubWindow(self.parent, 'Channel Window')
        chgrpwidget.resize(640, 400)
        chgrpwidget.move(100, 100)

        clientarea = chgrpwidget.getclientarea()
        qtabwidget = QAdvancedTabWidget(clientarea)
        clientarea.setObjectName('Test')
        qtabwidget.setMovable(True)
        qtabwidget.show()

        # setup ability to right click on tab widget and get a menu
        #qtabwidget.contextMenuEvent = lambda event: self.tab_contextmenu_event(qtabwidget, event)

        chgrpwidget.qtabwidget = qtabwidget
        def __resizeEvent(event):
            qtabwidget.resize(clientarea.width(), clientarea.height())
        clientarea.resizeEvent = __resizeEvent
        # make console widgets
        css = self.parent.styleSheet()
        for changrptitle in channelgroups:
            channels = channelgroups[changrptitle]
            console = self.createchannel(chgrpwidget, channels, changrptitle)
            if '$all' in channels:
                allconsole = console
        # save the sub-window and tab widget
        self.chgrpwidgets.append([chgrpwidget, qtabwidget, channels])
        chgrpwidget.show()
        qtabwidget.show()

        if allconsole is not None:
            qtabwidget.setCurrentWidget(allconsole)

        return chgrpwidget


