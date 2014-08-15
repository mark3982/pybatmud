from pkg.qconsolewindow import QConsoleWindow
from pkg.game import Priority

class QPlugUnknown(QConsoleWindow):
    """Provides debugging output.

    This widget is used to provide debugging and early testing output. It is not
    intended to be used in production or by normal end users under normal circumstances.
    If this provides production or normal functionality then that which it provides 
    should be moved to a another extension when possible.
    """
    def __init__(self, pwin, game):
        super().__init__(pwin, 'Master Console')
        self.game = game

        self.resize(800, 500)

        game.registerforevent('prompt', self.event_prompt, Priority.Normal)
        game.registerforevent('banner', self.event_banner, Priority.Normal)
        game.registerforevent('unknown', self.event_unknown, Priority.Normal)

    def event_unknown(self, event, line):
        self.processthenaddline(line)

    def commandEvent(self, command):
        self.game.command(command)

    def event_prompt(self, event, prompt):
        self.setprompt(prompt, fgdef = 'xprompt')

    def event_banner(self, event, lines):
        for line in lines:
            line = line.decode('utf8')
            line = line.replace(' ', '&nbsp;')
            self.addline(line)
