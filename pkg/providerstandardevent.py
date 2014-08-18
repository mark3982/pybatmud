"""Implements ProviderStandardEvent Object

    I think eventually I will add more support to using the
    batmud client extension stuff, but for now we are mainly
    just ignoring most of it except the color. --kmcg
"""
import time

from pkg.game import Priority

def onlychars(chars, line):
    for c in line:
        if c not in chars:
            return False
    return True

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
        self.game.registerforevent('lineunknown', self.event_lineunknown, Priority.High)
        self.game.registerforevent('blockunknown', self.event_blockunknown, Priority.High)
        self.game.registerforevent('chunkunknown', self.event_chunkunknown, Priority.High)

        self.game.registerforevent('blockrefined', self.event_blockrefined, Priority.High)
        self.readbanner = True
        self.droploginopts = False
        self.banner = []

        # my weird way of handling weird crap
        self.blockrefinedhold = b''

    def stripofescapecodes(self, line):
        # remove crazy escape codes
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

        line = line.decode('utf8', 'replace')

        parts = line.split('\x1b')

        line = []

        for part in parts:
            part = part[part.find('m') + 1:]
            line.append(part)

        return ''.join(line)

    def handleprompt(self, line):
        if len(line) < 1:
            return
        # let us extract the prompt and produce an event
        # with the information that it contains
        self.game.pushevent('prompt', line)

        # i could optmize this a bit.. but its hardly called so
        # i opted for code size reduction and readability

        # let us check if it is a continue type prompt
        if line.find(b'More') > -1 and line.find(b'[qpbns?]') > -1:
            self.game.pushevent('moreprompt', line)
            return

        # let us see if it is a prompt that contains health information
        if line.find(b'Hp') > -1 and line.find(b'Sp') > -1 and line.find(b'Ep') > -1 and line.find(b'Exp') > -1:
            line = self.stripofescapecodes(line)
            # drop any crap at the beginning (sometimes 0x01 gets there.. yea i know..)
            line = line[line.find('Hp'):]
            # let us also try to parse the prompt
            parts = line.strip().split(' ')
            hp = parts[0]       # health 
            sp = parts[1]       # skill
            ep = parts[2]       # endurance
            ex = parts[3]       # experience
            hp = hp[hp.find(':') + 1:].split('/')
            sp = sp[sp.find(':') + 1:].split('/')
            ep = ep[ep.find(':') + 1:].split('/')
            ex = int(ex[ex.find(':') + 1:])
            hp = (int(hp[0]), int(hp[1]))
            sp = (int(sp[0]), int(sp[1]))
            ep = (int(ep[0]), int(ep[1]))
            self.game.pushevent('stats', hp, sp, ep, ex)
            return
        return

    def _procline(self, line):
        while line[-1].find(b'\n') > -1:
            out = b''.join(line)
            self.event_rawunknown(None, out[0:out.find(b'\n')].strip())
            line = [out[out.find(b'\n') + 1:]]
        return line

    def event_blockunknown(self, event, block):
        if block.find(b'\x1b<10spec_map\x1b|NoMapSupport\x1b>10') == 0:
            return True

        # ignore this until we can do something with it later
        if block.find(b'\x1b<99BAT_MAPPER') == 0:
            return True

        # look for the odd unwrapped sequence of blocks
        parts = block.split(b'\x1b')

        if len(parts[0]) > 0:
            raise Exception('Not Block')

        line = []

        for x in range(1, len(parts)):
            part = parts[x]
            if part[0] == ord('<'):
                if part[1:3] == b'20':
                    # color code
                    hexcolor = part[3:]
                    try:
                        tmp = int(hexcolor, 16)
                        hexcolor = hexcolor.ljust(6, b'0')
                        line.append(b'\x1b#' + hexcolor + b';')
                    except ValueError:
                        pass
                continue
            if part[0] == ord('>'):
                rem = part[3:]
                line.append(b'\x1b[m')
                line.append(rem)
                continue
            if part[0] == ord('['):
                rem = b'\x1b' + part
                line.append(rem)
                continue
            if part[0] == ord('|'):
                rem = part[1:]
                line.append(rem)
                continue
        # handle special block prompt
        if block.find(b'\x1b<10spec_prompt') == 0:
            self.handleprompt(b''.join(line))
            return
        #\x1b<41summon_rift_entity 9\x1b>41....
        if block.find(b'\x1b<41') == 0:
            line = block[4:block.find(b'\x1b', 1)]
            line = line.split(b' ')
            spellname = line[0].decode('utf8')
            spellticks = line[1].decode('utf8')
            self.game.pushevent('spelltick', spellname, spellticks)
            return
        #<10chan_newbie\x1b|\x1b[1;33mToffzen [newbie]: a boost\x1b[m\r\n\x1b>10
        if block.find(b'\x1b<10chan_') == 0:
            pass

        line = b''.join(line)
        self.game.pushevent('blockrefined', line)
        return

    def event_chunkunknown(self, event, chunk):
        self.blockrefinedhold = self.blockrefinedhold + chunk

    def event_blockrefined(self, event, block):
        # try to break this into lines if at all possible, and anything that can not be made into a line lets just
        # hold on to it until we can make a line...
        lines = block.split(b'\n')

        for x in range(0, len(lines) - 1):
            self.game.pushevent('lineunknown', lines[x].strip(b'\r'))

        self.blockrefinedhold = self.blockrefinedhold + lines[-1]

    def event_lineunknown(self, event, line):
        """Provides some standard higher level events.

        This is mainly going to take unknown events, which are the most basic
        and primitive event, and translate them into higher level events which
        reduces the code duplication that would be required by other extensions.

        It also reduces bugs and makes code more readable and compact by doing
        the most commonly needed things in this provider. If an extension is forced
        to interpret unknown events then it might be a good idea to put that code 
        here.
        """
        # anything in hold under block refined should be prefixed onto this line
        if len(self.blockrefinedhold) > 0:
            line = self.blockrefinedhold + line
            self.blockrefinedhold = b''
            # cancel this event.. create new event but with entire line
            self.game.pushevent('lineunknown', line)
            return True

        # we are done with login options
        if self.droploginopts and line.strip().startswith(b'3 - '):
            self.droploginopts = False
            self.game.pushevent('login')
            return True

        if self.droploginopts:
            # just discard this crap
            return True

        # disable reading of banner and read up options
        if self.readbanner: 
            if line.strip().startswith(b'1 - '):
                self.game.pushevent('banner', self.banner)
                self.readbanner = False
                self.droploginopts = True
                return True

        # let us grab the entire banner for safe keeping
        if self.readbanner:
            self.banner.append(line)
            return True

        # get ourselves a pure string which is easier to work with
        _line = self.stripofescapecodes(line)

        parts = _line.split(' ')
        if len(parts) > 3:
            if parts[1] == 'tells' and parts[2] == 'you' and parts[3].startswith("'"):
                who = parts[0]
                msg = ' '.join(parts[3:]).strip("'")
                self.game.pushevent('tell', who, msg, line)

        # channel messages
        pc = _line.find('):') 
        po = _line.find('(')
        tc = _line.find('>:')
        to = _line.find('<') 
        cc = _line.find('}:')
        co = _line.find('{') 
        sc = _line.find(']:')
        so = _line.find('[')

        namechars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_'

        # decide which are valid
        li = []
        if po > -1 and pc > -1 and pc > po:
            li.append((po, pc))
        if to > -1 and tc > -1 and tc > to:
            li.append((to, tc))
        if co > -1 and cc > -1 and cc > co:
            li.append((co, cc))
        if so > -1 and sc > -1 and sc > so:
            li.append((so, sc))

        # find the lowest
        _lhv = 999999
        _lhi = None
        for l in li:
            if l[0] < _lhv:
                _lhv = l[0]
                _lhi = l

        if _lhi is not None:
            uo = _lhi[0]
            uc = _lhi[1]

            if uc == 0:
                # {bat}: Woocca shakes the magic 8 ball, and it reveals: My Sources Say No.\x1b[m\r\n'
                chname = _line[uo + 1:uc]
                tmp = _line[uc + 1].strip().split(' ')
                chwho = tmp[0]
                chmsg = ' '.join(tmp[1:])
            else:
                # kmcg [bat]: hello world
                chwho = _line[0:uo]
                chmsg = _line[uc + 2:]
                chname = _line[uo + 1:uc]
            self.game.pushevent('channelmessage', chname, chwho, chmsg, line)

        # rift walker entity support for events
        if _line.startswith('--=') and _line.find('=--') == len(_line) - 3:
            # give the event handler the actual complete message
            self.game.pushevent('riftentitymessage', line)
            # strip codes from it
            # let us also try to process it 
            ename = _line[0:_line.find('HP')].strip()
            parts = _line[_line.find('HP'):].split(' ')
            hp = parts[0]               # set variable
            hpchg = parts[1]            # set variable
            hp = hp[hp.find(':')+1:-1]  # drop crap
            hp = hp.split('(')          # split into parts
            hp = (int(hp[0]), int(hp[1]))         # turn into tuple
            hpchg = hpchg.strip('()')
            self.game.pushevent('riftentitystats', ename, hp)
            return








