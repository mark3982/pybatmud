"""Implements ProviderStandardEvent Object

    I think eventually I will add more support to using the
    batmud client extension stuff, but for now we are mainly
    just ignoring most of it except the color. --kmcg
"""
import time

from pkg.game import Priority
from pkg.dprint import dprint

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
        self.privmsg_nextline_tome = False
        self.privmsg_nextline_fome = False
        # we are mainly concerned with translating unknown events into higher level events
        self.game.registerforevent('lineunknown', self.event_lineunknown, Priority.High)
        self.game.registerforevent('blockunknown', self.event_blockunknown, Priority.High)
        self.game.registerforevent('chunkunknown', self.event_chunkunknown, Priority.High)
        self.game.registerforevent('prompt', self.event_prompt, Priority.High)
        self.game.registerforevent('blockrefined', self.event_blockrefined, Priority.High)
        self.game.registerforevent('connected', self.event_connected, Priority.High)

    def event_connected(self, event):
        self.readbanner = True
        self.droploginopts = False
        self.banner = []
        self.seenattention = False
        # my weird way of handling weird crap
        self.blockrefinedhold = b''

    def event_prompt(self, event, line):
        if len(line) < 1:
            return

        # i could optmize this a bit.. but its hardly called so
        # i opted for code size reduction and readability
        if line.find(b'What is your name:') == 0:
            if not self.seenattention:
                self.game.pushevent('login')
            return

        # let us check if it is a continue type prompt
        if line.find(b'More') > -1 and line.find(b'[qpbns?]') > -1:
            self.game.pushevent('moreprompt', line)
            return

        # let us see if it is a prompt that contains health information
        if line.find(b'Hp') > -1 and line.find(b'Sp') > -1 and line.find(b'Ep') > -1 and line.find(b'Exp') > -1:
            _line = self.game.stripofescapecodes(line)
            # drop any crap at the beginning (sometimes 0x01 gets there.. yea i know..)
            _line = _line[_line.find('Hp'):]
            # let us also try to parse the prompt
            parts = _line.strip().split(' ')
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
                        line.append(b'\x1b#' + hexcolor + b'm')
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

        line = b''.join(line)

        '''
            At this point we have converted the block into a refined block which
            means we have extracted the visual text from the block and converted
            any formatting codes into terminal escape codes. The refined block 
            may contain multiple lines or a partial line. The refined block does
            NOT contain any telnet extension codes or data which is important for
            the next stages of the pipeline.

            In some cases we grab the block and refined block and use them creating
            a new event, but we return and do not pass it onward to the refined block
            event because it would either produce no visual text or the text it would
            produce should not be displayed.

            The refined block is known as `line` which is confusing, but it really
            should be `rblock`.

            The refined block will if not dropped continue onward to the refined block
            which will break it into lines to be processed by the `unknownline` event.

            There are cases where part of a refined block is left over. This will simply
            be prepended to the next line or refined block that comes through the pipeline.
        '''

        #b:b'\x1b<10spec_battle\x1b|Shaking pigeon scratches Fire entity making small marks.\r\n\x1b>10'
        if block.find(b'\x1b<10spec_battle') == 0:
            _line = line.replace(b'\r', b'')
            _line = _line.replace(b'\n', b'')
            self.game.pushevent('battlemessage', _line)

        #b:b'\x1b<70Shaking_pigeon 100\x1b>70'
        if block.find(b'\x1b<70') == 0:
            body = block[block.find(b'0') + 1:block.rfind(b'\x1b')]
            body = body.decode('utf8', 'ingnore').split(' ')
            mname = body[0]
            mhealth = int(body[1])
            self.game.pushevent('mobhealth', mname, mhealth)
            # its not going to get displayed anyway so no need to
            # try pushing it onward to refine block
            return

        # handle special block prompt
        if block.find(b'\x1b<10spec_prompt') == 0:
            self.game.pushevent('prompt', line)
            return

        #b:b'\x1b<41summon_rift_entity 9\x1b>41'
        #b:b'\x1b<41heal_self 1\x1b>41'
        if block.find(b'\x1b<41') == 0:
            line = block[4:block.find(b'\x1b', 1)]
            line = line.split(b' ')
            spellname = line[0].decode('utf8')
            spellticks = line[1].decode('utf8')
            self.game.pushevent('spelltick', spellname, int(spellticks))
            return

        #b:b'\x1b<52Kmcg 0 brownie 21 1 24762\x1b>52'
        if block.find(b'\x1b<52') == 0:
            body = block[block.find(b'2') + 1:block.rfind(b'\x1b')]
            parts = body.decode('utf8', 'ignore').split(' ')
            name = parts[0]
            unknown = parts[1]
            xclass = parts[2]
            level = int(parts[3])
            self.game.pushevent('playerstatus', '$me', xclass, level)
            return

        #b:b'\x1b<10chan_sales\x1b|Broetchen {sales}: sold\r\n\x1b>10'
        #b:b'\x1b<10chan_newbie\x1b|\x1b[1;33mToffzen [newbie]: a boost\x1b[m\r\n\x1b>10'
        #b:b"\x1b<10chan_sky-\x1b|Faisel (sky-): 'use plant lore at carrot'\r\n\x1b>10'"
        #b:b'\x1b<10chan_wanted\x1b|Choboeio [wanted]: acid/mana gaiters\r\n\x1b>10'
        #b:b'\x1b<10chan_sales\x1b|Choboeio [sales]: w: acid/mana gaiters\r\n\x1b>10'
        #b:b'\x1b<10chan_party\x1b|\x1b[1;35mKmcg [party]: test\x1b[m\r\n\x1b>10'
        #b:b'\x1b<10chan_sky-\x1b|Shedevil [sky-]: why i got leads :D\r\n\x1b>10'
        if block.find(b'\x1b<10chan_') == 0:
            _line = self.game.stripofescapecodes(line)

            # figure out what type of symbols surround the channel name
            head = _line[0:_line.find(':')]
            syms = None
            if head.find('[') > -1:
                syms = '[]'
            if head.find('{') > -1:
                syms = '{}'
            if head.find('<') > -1:
                syms = '<>'
            if head.find('(') > -1:
                syms = '()'
            if syms is None:
                print('OOPS', line, _line)
            else:
                chwho = _line[0:_line.find(' ')]
                chname = _line[_line.find(syms[0]) + 1:_line.find(syms[1])]
                chmsg = _line[_line.find(':') + 1:].strip()
                _line = line.replace(b'\n', b'')
                _line = _line.replace(b'\r', b'')
                self.game.pushevent('channelmessage', chname, chwho, chmsg, _line)
            # im going to let it goto the lineunknown so it will be displayed
            # in the all window.. --kmcg

        #b:b'\x1b<62Kmcg brownie 1 21 198 198 620 620 204 204 fire_builders 1 1 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 524 Wed_Aug_20_19:46:15_2014\x1b>62'
        #b:b'\x1b<62Wick barsoomian 1 92 902 902 31 31 398 398 fire_builders 2 1 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 524 Wed_Aug_20_19:46:15_2014\x1b>62'

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

        # get ourselves a pure string which is easier to work with
        _line = self.game.stripofescapecodes(line)

        # tell messages continuation (doing it the old school way)
        if self.privmsg_nextline_tome is not False:
            # if we have still not found it then.. keep looking
            if _line[-1] != "'":
                self.privmsg_nextline_tome.append(line)
                return
            line = b''.join(line)
            self.privmsg_nextline_tome = False
            self.game.pushevent('tell', who, '$me', msg, line)
            return
        if self.privmsg_nextline_fome is not False:
            if _line[-1] != "'":
                # keep reading lines until we find the terminating one
                self.privmsg_nextline_fome.append(line)
                return
            who = self.privmsg_nextline_fome[0]
            line = b''.join(self.privmsg_nextline_fome[1:])
            self.privmsg_nextline_fome = False
            self.game.pushevent('tell', who, '$me', line)
            return

        # disable reading of banner and read up options
        if self.readbanner: 
            if line.strip().startswith(b'1 - '):
                self.game.pushevent('banner', self.banner)
                self.readbanner = False

        # let us grab the entire banner for safe keeping
        if self.readbanner:
            self.banner.append(line)
            return True

        # block login event from being produced after this
        if _line == '======[ ATTENTION ]==================================================':
            self.seenattention = True
            return

        parts = _line.split(' ')
        if len(parts) > 3:
            if parts[1] == 'tells' and parts[2] == 'you' and parts[3].startswith("'"):
                who = parts[0]
                msg = ' '.join(parts[3:]).strip("'")
                if _line[-1] != "'":
                    self.privmsg_nextline_tome = [who, line]
                else:
                    self.game.pushevent('tell', who, '$me', line)
                return

            #l:b"\x1b[1;37mYou tell Wick 'how many you done so far?'\x1b[0m"
            if parts[0] == 'You' and parts[1] == 'tell':
                who = parts[2]
                msg = _line[_line.find('\'') + 1:].strip('\'')
                if _line[-1] != "'":
                    self.privmsg_nextline_fome = [who, line]
                else:
                    self.game.pushevent('tell', '$me', who, line)
                return
            # it was not part of a tell message

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








