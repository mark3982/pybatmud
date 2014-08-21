import time

from PyQt4 import QtGui
from PyQt4 import QtCore

from pkg.qsubwindow import QSubWindow
from pkg.dprint import dprint

class QPlugSpellMan(QSubWindow):
    def __init__(self, pwin, game):
        super().__init__(pwin)
        self.game = game

        self.spells = {}

        self.resizeon(False)

        game.registerforevent('spellspec', self.event_spellspec)
        game.registerforevent('spelltick', self.event_spelltick)
        game.registerforevent('lineunknown', self.event_lineunknown)

        self.ticktimer = QtCore.QTimer(self)
        self.ticktimer.timeout.connect(self.tick)
        self.ticktimer.start(100)

        self.move(400, 30)
        self.resize(400, 30)

        self.desc = QtGui.QLabel(self)
        self.desc.resize(self.width(), self.height())
        self.desc.setText('Spell/Skill Monitor')
        self.desc.setObjectName('SpellDesc')
        self.desc.resize(self.width(), self.height())
        self.desc.setAlignment(QtCore.Qt.AlignCenter)

        self.show()

        self.tickinterval = 2.857

    def event_spellspec(self, event, line):
        #b:b'\x1b<10spec_skill\x1b|Wick hunts about for wood, gathering up small sticks and brush\r\nto make a small fire.\r\n\x1b>10'
        #b:b"\x1b<10spec_spell\x1b|You clap your hands and whisper 'judicandus littleee'\r\n\x1b>10"
        pass

    def event_lineunknown(self, event, line):
        #l:b'You are done with the chant.\x1b[0m'
        if line.find(b'You are done with the chant.') == 0:
            # let us terminate the current spell since it is over
            myspells = self.spells['$me']
            for spellname in myspells:
                myspells[spellname][2] = 0

    def tick(self):
        self.update()

    def event_spelltick(self, event, spellname, spelltick):
        if '$me' not in self.spells:
            self.spells['$me'] = {}
        if spellname not in self.spells['$me']:
            w = QtGui.QFrame(self)
            l = QtGui.QLabel(self)
            l.move(0, 0)
            w.setObjectName('SpellBar')
            w.show()
            l.setObjectName('SpellBarText')
            l.setAlignment(QtCore.Qt.AlignCenter)
            l.show()
            # i do not know why we get sent a zero, but just
            # place at least two seconds on the clock because
            # we are likely to get another zero and then we
            # can slow it down instead of making the progress
            # bar jump around
            if spelltick == 0:
                spelltick = 2

            self.spells['$me'][spellname] = [w, l, spelltick, spelltick, time.time(), 1 / self.tickinterval]
        else:
            if spelltick > 0:
                # get time between ticks
                tbt = time.time() - self.spells['$me'][spellname][4]
                self.tickinterval = (self.tickinterval + tbt) / 2

                self.spells['$me'][spellname][2] = spelltick
                self.spells['$me'][spellname][4] = time.time()
                self.spells['$me'][spellname][5] = 1 / self.tickinterval
            else:
                # slow it down (essentially double it).. i do not
                # know why we get sent a zero but it usually indicates
                # that the spell has at least one second left
                self.spells['$me'][spellname][5] *= 0.5


    def update(self):
        if len(self.spells) < 1:
            return
        self.resize(self.width(), len(self.spells) * 30)
        hpe = self.height() / len(self.spells)

        ct = time.time()

        cy = 0
        for who in self.spells:
            toremove = []
            for spellname in self.spells[who]:
                spell = self.spells[who][spellname]
                w = spell[0]
                l = spell[1]
                c = spell[2]
                m = spell[3]
                st = spell[4]

                # get current tick in real time (counting seconds per #)
                cc = c - (ct - st) * 0.35

                if cc < 0 or m <= 0:
                    toremove.append(spellname)
                    continue

                width = (cc / m) * self.width()

                w.move(0, cy)
                w.resize(width, hpe)
                l.move(0, cy)
                l.resize(self.width(), hpe)
                l.setText('%s (%.01f)' % (spellname.replace('_', ' '), cc))
                l.raise_()
                cy = cy + hpe
            for r in toremove:
                spell = self.spells[who][r]
                w = spell[0]
                l = spell[1]
                l.hide()
                l.setParent(None)
                w.hide()
                w.setParent(None)
                del self.spells[who][r]
                dprint('removed spell', r)




