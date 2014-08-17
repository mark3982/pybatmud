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
            'Wanted':   ('#wanted',),
            'Newbie':   ('#newbie',),
            'Ghost':    ('#ghost',),
        })

        game.registerforevent('prompt', self.event_prompt, Priority.Normal)
        game.registerforevent('banner', self.event_banner, Priority.Normal)
        game.registerforevent('unknown', self.event_unknown, Priority.Normal)
        game.registerforevent('channelmessage', self.event_channelmessage, Priority.Normal)
        game.registerforevent('tell', self.event_tell, Priority.Normal)

    def event_channelmessage(self, event, chan, who, msg, line):
        chan = ('#%s' % chan).lower()
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                page = tabctrl.widget(i)
                chanlist = page.chanlist
                if chan in chanlist:
                    page.processthenaddline(line)
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
            self.event_unknown(event, item)
    def event_tell(self, event, who, msg, line):
        """Route tell to appropriate channel.

        We route the tell to the appropriate channel by first looking
        for a channel that will accept it. We also route it to any 
        channel that has a $tell input. If we do not find a channel
        that accepts it without using the $tell input then we create
        a new channel with that input only.
        """
        who = '!%s' % who
        delivered = False
        for chgrp in self.chgrpwidgets:
            tabctrl = chgrp[1]
            for i in range(0, tabctrl.count()):
                page = tabctrl.widget(i)
                if who in page.chanlist:
                    page.processthenaddline(line)
                    delivered = True
                if '$tells' in page.chanlist:
                    page.processthenaddline(line)
        if delivered is False:
            # ok we did not find a window to handle this.. so we need
            # to create a channel in a window that can handle it
            pass

    def event_unknown(self, event, line):
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
                page = tabctrl.widget(i)
                chanlist = page.chanlist
                if '$all' in chanlist:
                    page.processthenaddline(line)

    def commandEvent(self, line):
        """When the command input on any channel window changes.
        """
        # set history line
        self.chistory[-1] = line
        # make new history line
        self.chistory.append('')
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

    def createchannel(self, tabwidget, channels):
        """Create channel in specified channel group.
        """
        css = self.parent.styleSheet()
        qconsole = QConsoleWindow(None, css)
        qconsole.setupdowncallback(self.updowncallback)
        qconsole.setcommandchangedcallback(self.commandchangedcallback)
        tabwidget.addTab(qconsole, ', '.join(channels))
        qconsole.chanlist = channels
        qconsole.commandEvent = self.commandEvent
        qconsole.show()

    def createchannelgroup(self, channelgroups = {}):
        """Create a new channel group window.
        """
        css = self.parent.styleSheet()
        chgrpwidget = QSubWindow(self.parent, 'Channel Window')
        chgrpwidget.resize(600, 400)
        clientarea = chgrpwidget.getclientarea()
        qtabwidget = QtGui.QTabWidget(clientarea)
        qtabwidget.setObjectName('ChannelTab')
        def __resizeEvent(event):
            qtabwidget.resize(clientarea.width(), clientarea.height())
        clientarea.resizeEvent = __resizeEvent
        # make console widgets
        css = self.parent.styleSheet()
        for changrptitle in channelgroups:
            channels = channelgroups[changrptitle]
            self.createchannel(qtabwidget, channels)
        # save the sub-window and tab widget
        self.chgrpwidgets.append([chgrpwidget, qtabwidget, channels])
        chgrpwidget.show()
        qtabwidget.show()


