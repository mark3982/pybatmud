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

