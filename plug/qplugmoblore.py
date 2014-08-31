import os.path
import itertools

from PyQt4 import QtCore
from PyQt4 import QtGui
from pkg.qsubwindow import QSubWindow
from pkg.dprint import dprint
from pkg.game import Priority

def findmulti(s, m, pos = 0):
    lv = None
    for _m in m:
        v = s.find(_m, pos)
        if v > -1 and (lv is None or v < lv):
            lv = v
    return lv

class QPlugMobLore(QSubWindow):
    """Provides Mob Lore Plugin.

    This provides the information gathering plugin mob lore.
    """
    def __init__(self, pwin, game):
        super().__init__(pwin)
        self.pwin = pwin
        self.game = game

        self.hide()

        self.game.registerforevent('blockunknown', self.event_blockunknown, Priority.VeryHigh)
        self.game.registerforevent('lineunknown', self.event_lineunknown, Priority.VeryHigh)
        self.game.registerforevent('mobdetected', self.event_mobdetected)
        self.game.registerforevent('playerstatus', self.event_playerstatus)

        self.moblore = self.loadlore()

        required = {
            'invalid-words': set(),
            'consider-base':  {},
            'consider-full':  {},
            'descnametoname': {},
            'looks':          {}
        }

        for r in required:
            if r not in self.moblore:
                self.moblore[r] = required[r]

        self.pendingconsiders = []
        self.pendinglooks = []

        self.consider_intercept = False
        self.look_intercept = False
        self.tmp = []

        self.playerlevel = -1

    def event_playerstatus(self, event, who, xclass, level):
        if who == '$me':
            self.playerlevel = level

    def loadlore(self):
        # very simple and safe storage.. but slow
        if os.path.exists('moblore'):
            fd = open('moblore', 'r')
            data = fd.read().strip()
            fd.close()
            if len(data) > 0:
                moblore = eval(data)
                return moblore
        return {}

    def dumplore(self):
        # very simple and safe storage.. but slow
        fd = open('moblore', 'w')
        fd.write('%s' % self.moblore)
        fd.close()

    def event_blockunknown(self, event, block):
        #b:b'\x1b<10spec_skill\x1b|The final estimation is that Caretaker of the Temple can easily reduce you to\r\nminced meat, so run for your life.\r\n\x1b>10'
        #b:b'\x1b<10spec_skill\x1b|The final estimation is that Monarch butterfly looks quite skilled, beware.\r\n\x1b>10'
        #b:b"\x1b<10spec_skill\x1b|The final estimation is that Warthog's power overwhelms your mind! You PANIC!!\r\n\x1b>10"
        if block.find(b'\x1b<10spec_skill\x1b|The final estimation is that') == 0:
            i = block.find(b'that') + 5
            x = findmulti(block, (b'can', b'looks', b'power', b'and', b'has'), i)
            mob_basename = block[i:x].strip()
            desc = block[x:]

            if mob_basename.endswith(b'\'s'):
                mob_basename = mob_basename[0:-2]

            mob_basename = mob_basename.decode('utf8')
            desc = desc.decode('utf8')
            if desc.find('\r') > -1:
                desc = desc[0:desc.find('\r')].strip()

            print('mob_basename:[%s] desc:[%s]' % (mob_basename, desc))

            if self.consider_intercept:
                entry = self.pendingconsiders.pop(0)
                self.moblore['descnametoname'][entry[1]] = mob_basename
            else:
                entry = None

            mylevel = self.playerlevel

            # if we do not have our level then the consideration
            # can be quite meaningless really... right?
            if mylevel > -1:
                if mylevel not in self.moblore['consider-base']:
                    self.moblore['consider-base'][mylevel] = {}
                if mylevel not in self.moblore['consider-full']:
                    self.moblore['consider-full'][mylevel] = {}
                self.moblore['consider-base'][mylevel][mob_basename] = desc
                if entry is not None:
                    self.moblore['consider-full'][mylevel][entry[1]] = desc
                self.game.pushevent('lineunknown', b'\x1b#99ff99mAdded level of [' + bytes(mob_basename, 'utf8') + b'] to MOB-LORE.')
                self.dumplore()

            if self.consider_intercept:
                self.consider_intercept = False                
                # remove everything else to keep from just wasting
                # bandwidth and time trying them when we have already
                # found the correct one
                _pendingconsiders = []
                for p in self.pendingconsiders:
                    if p[1] != entry[1]:
                        _pendingconsiders.append(p)
                self.pendingconsiders = _pendingconsiders

                self.pendinglooks.append(mob_basename)
                self.do_nextconsider()
                return True
            else:
                # take a quick look at the mob
                dprint('doing quick look at [%s]' % mob_basename)
                self.game.lockcmdgroup(self)
                self.pendinglooks.append(mob_basename)
                self.do_nextlook()
        elif block.find(b'\x1b<10spec_skill') == 0 and self.consider_intercept:
            # drop it
            return True

    def mobfullpermutations(self, mobfull):
        out = []
        out.append(mobfull)

        mobfull = mobfull.split(' ')

        for l in range(len(mobfull) - 1, 0, -1):
            for x in range(0, len(mobfull)):
                if x + l > len(mobfull):
                    continue
                s = []
                for y in range(0, l):
                    s.append(mobfull[x + y])
                s = ' '.join(s)
                out.append(s)
        return out


    def event_mobdetected(self, event, mob):
        if mob in self.moblore['descnametoname']:
            # shortcut it since we have seen it before
            phrase = self.moblore['descnametoname'][mob]
            self.pendingconsiders.append((phrase, mob))
        else:
            totry = self.mobfullpermutations(mob)
            for phrase in totry:
                # its worth the cpu considering the latency
                # and bandwidth we save...
                if phrase not in self.pendingconsiders:
                    self.pendingconsiders.append((phrase, mob))

        self.game.lockcmdgroup(self)
        self.do_nextconsider()

    def do_nextlook(self):
        if len(self.pendinglooks) < 1:
            self.game.unlockcmdgroup(self)
            return

        # only look at things we have never looked at before
        while True:
            if len(self.pendinglooks) < 1:
                self.game.unlockcmdgroup(self)
                return
            phrase = self.pendinglooks[0]
            if phrase in self.moblore['looks']:
                dprint('[%s] already in looks' % phrase)
                self.pendinglooks.pop(0)
                continue
            break

        self.look_intercept = True
        self.tmp = []
        self.game.command('look %s' % phrase, self)

    def do_nextconsider(self):
        if not self.consider_intercept:
            if len(self.pendingconsiders) < 1:
                # unlock command group and exit since
                # we have finished doing our considers
                self.do_nextlook()
                return  
            phrase = self.pendingconsiders[0][0]
            self.consider_intercept = True
            dprint('considering `%s`' % phrase)
            self.game.command('consider %s' % phrase, self)

    def event_lineunknown(self, event, line):
        #l:b'A little bunny is such a sweet sight, fluffy like a ball of cotton and as'
        #l:b'white too. You cannot help but adore this tiny cute animal.'
        #l:b'He is in excellent shape.'
        #l:b'He looks hungry.'
        if self.look_intercept:
            # He looks
            # She looks
            # It looks
            x = line.find(b'looks')
            if x < 6 and x > -1:
                # ignore this line
                return True
            if line.endswith(b'shape.'):
                tmp = ' '.join(self.tmp)
                phrase = self.pendinglooks.pop(0)
                self.game.pushevent('lineunknown', b'\x1b#99ff99mAdded looks of [' + bytes(phrase, 'utf8') + b'] to MOB-LORE.')
                self.moblore['looks'][phrase] = tmp
                self.dumplore()
                self.look_intercept = False
                self.do_nextlook()
                return True
            self.tmp.append(line.decode('utf8'))
            return True


        #l:b'That is not possible.'
        if line.find(b'That is not possible.') == 0 and self.consider_intercept:
            self.consider_intercept = False
            # do nothing because it was invalid
            entry = self.pendingconsiders.pop(0)
            self.do_nextconsider()
            return True

        # At the moment these are useless 
        #l:b'You make a small puddle on the floor.'
        #if line.find(b'You make a small puddle on the floor.') == 0 and self.consider_intercept:
        #    return True
        #l:b"Not a valid adverb, 'blurred'."
        #if line.find(b'Not a valid adverb, ') == 0 and self.consider_intercept:
        #    return True

        #l:b'\x1b[1;32msix spotted ladybird\x1b[0m'
        if line.find(b'\x1b[1;32m') == 0 and line.count(b'\x1b') == 2 and line.find(b':') < 0:
            mob = line[line.find(b'm') + 1:line.rfind(b'\x1b')].decode('utf8', 'ignore')
            mob = mob.replace(',', '')
            if mob.find(' is') > -1:
                mob = mob[0:mob.find(' is')].strip()
            if mob.startswith('a '):
                mob = mob[2:]
            if mob.startswith('A '):
                mob = mob[2:]
            dprint('mob:%s' % mob)
            self.game.pushevent('mobdetected', mob)

