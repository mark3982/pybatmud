from pkg.game import Priority

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
        self.game.registerforevent('unknown', self.event_unknown, Priority.High)
        self.readbanner = True
        self.droploginopts = False
        self.banner = []

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

        return ''.join(part)

    def event_unknown(self, event, line):
        """Provides some standard higher level events.

        This is mainly going to take unknown events, which are the most basic
        and primitive event, and translate them into higher level events which
        reduces the code duplication that would be required by other extensions.

        It also reduces bugs and makes code more readable and compact by doing
        the most commonly needed things in this provider. If an extension is forced
        to interpret unknown events then it might be a good idea to put that code 
        here.
        """

        # we are done with login options
        if self.droploginopts and line.startswith(b'3 - '):
            self.droploginopts = False
            self.game.pushevent('login')
            return True

        if self.droploginopts:
            # just discard this crap
            return True

        # disable reading of banner and read up options
        if self.readbanner: 
            if line.startswith(b'1 - '):
                self.game.pushevent('banner', self.banner)
                self.readbanner = False
                self.droploginopts = True
                return True

        # let us grab the entire banner for safe keeping
        if self.readbanner:
            self.banner.append(line)
            return True

        # lets us try to figure out what it could be..
        # remove crazy escape codes
        parts = line.split(b'\xff')
        
        line = []
        line.append(parts[0])

        for x in range(1, len(parts)):
            part = parts[x]
            if part[0] == 0xf9:
                line = b''.join(line)

                if line[0] == 0x1:
                    line = line[1:]
                # let us extract the prompt and produce an event
                # with the information that it contains
                self.game.pushevent('prompt', line)

                # i could optmize this a bit.. but its hardly called so
                # i opted for code size reduction and readability

                # let us check if it is a continue type prompt
                if line.find(b'More') > 0 and line.find(b'[qpbns?]') > 0:
                    self.game.pushevent('moreprompt', line)

                # let us see if it is a prompt that contains health information
                if line.find(b'Hp') > 0 and line.find(b'Sp') > 0 and line.find(b'Ep') > 0 and line.find(b'Exp') > 0:
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
                line = []
            line.append(part[1:])
        line = b''.join(line)

        # rift walker entity support for events
        if line.startswith(b'--=') and line.find(b'=--') == len(line) - 3:
            # give the event handler the actual complete message
            self.game.pushevent('riftentitymessage', line)
            print('riftentitymessage', line)
            # strip our TELNET and terminal codes so its a pure string
            line = self.stripofescapecodes(line)
            # i like strings if im not dealing with binary data
            line = line.decode('utf8')
            # drop the crap to simplify others processing it
            line = line[3:-4].strip()
            # strip codes from it
            # let us also try to process it 
            ename = line[0:line.find('HP')].strip()
            parts = line[line.find('HP'):].split(' ')
            hp = parts[0]               # set variable
            hpchg = parts[1]            # set variable
            hp = hp[hp.find(':')+1:-2]  # drop crap
            hp = hp.split('(')          # split into parts
            hp = (hp[0], hp[1])         # turn into tuple
            hpchg = hpchg.strip('()')
            self.game.pushevent('riftentitystats', ename, hp)
            print('riftentitystats', ename, hp)










