from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import QtWebKit

from pkg.qsubwindow import QSubWindow

'''
    These are used to manipulate hex colors. I mainly had to implement these
    to adjust the colors that the server sent for the batmud client extension.

    It was sending color codes for a bright blue that was honestly hard to read,
    so I used these function to adjust the blue component to not be so strong and
    to spread it onto the red and green components with `hexcolordimblue`. 

    I might need to write a better function that can automatically dim any component
    that becomes too bright thus handling any situation.
'''
def hexcolortotuple(hexcolor):
    return (int(hexcolor[0:2], 16), int(hexcolor[2:4], 16), int(hexcolor[4:6], 16))
def hexcolordimer(hexcolor, rf, gf, bf):
    r = int(hexcolor[0] * rf)
    g = int(hexcolor[1] * gf)
    b = int(hexcolor[2] * bf)
    return (r, g, b)
def hexcolordimblue(hexcolor, bf):
    r = hexcolor[0]
    g = hexcolor[1]
    b = hexcolor[2]
    diff = int(b * bf)
    #diff = hexcolor[2] - b
    #diff = int(diff * 0.5)

    r = r + diff
    g = g + diff
    if r > 0xff:
        r = 0xff
    if g > 0xff:
        g = 0xff
    return (r, g, b)
def tupletohexcolor(tup):
    return '%02x%02x%02x' % (tup[0], tup[1], tup[2])

class QConsoleWindow(QtGui.QWidget):
    """A Qt widget that provides a console like window.

    A Qt widget that provides a console like window with support for rendering
    terminal codes visually, and provides command input. This can be used to
    display select information such as game messages, channel messages, or even
    messages produced soley by the system.
    """
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.wp.resize(self.width() - 6, self.height() - (3 + 25))
        self.ce.move(2, self.height() - (25 + 3))
        self.ce.resize(self.width() - 5, 26)

    def keyPressEvent(self, event):
        """Helps ensure keystrokes go to the command box.
        """
        # we seem to be sent key press events even
        # if the command line box has focus, so we
        # need to check if it has focus, and if not
        # send it the key pressed then switch focus
        # to it
        if not self.ce.hasFocus():
            self.ce.setFocus()
            self.ce.keyPressEvent(event)
        # look for up and down arrows
        key = event.key()
        if key == QtCore.Qt.Key_Tab:
            # grab text from html
            plaintext = self.wp.page().mainFrame().toPlainText()[-4096:]
            plaintextlower = plaintext.lower()
            # grab command line
            cmdline = self.ce.text()
            if len(cmdline) > 0:
                # find last word of cmdline
                partialword = cmdline.split(' ')[-1].lower()
                posa = plaintextlower.rfind(' ' + partialword)
                posb = plaintextlower.rfind('\n' + partialword)
                posc = plaintextlower.rfind('\t' + partialword)

                if posa > posb:
                    pos = posa
                else:
                    pos = posb
                if posc > pos:
                    pos = posc

                if pos > -1:
                    # find last alphanumeric character after position `pos + 1`
                    for x in range(pos + 1, len(plaintext)):
                        if not plaintext[x].isalnum():
                            break

                    word = plaintext[pos + 1:x]
                    self.ce.setText(cmdline[0:cmdline.rfind(' ') + 1] + word)


        if key == QtCore.Qt.Key_Up or key == QtCore.Qt.Key_Down:
            if key == QtCore.Qt.Key_Up:
                up = True
            else:
                up = False
            if self.updowncallback is not None:
                self.updowncallback(up)
        if key == QtCore.Qt.Key_PageUp or key == QtCore.Qt.Key_PageDown:
            if key == QtCore.Qt.Key_PageUp:
                seg = -50
            else:
                seg = 50
            self.wp.page().mainFrame().evaluateJavaScript('window.scrollTo(0, document.body.scrollTop + %s);' % seg)    

    def hadfocus(self):
        return self._hadfocus

    def sethadfocus(self, val):
        self._hadfocus = val

    # little debugging and functionality inspection tool
    #def event(self, event):
    #    print('event', event)
    #    return super().event(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.sethadfocus(True)

    def _commandEvent(self):
        text = self.ce.text()       # get command box text
        self.ce.setText('')         # clear command box
        #self.setprompt(b'')         # clear prompt
        return self.commandEvent(text)

    def dummyKeyPressEvent(self, event):
        pass

    def commandchange_event(self):
        if self.commandchangedcallback is not None:
            self.commandchangedcallback(self.ce.text())

    def setcommandchangedcallback(self, cb):
        self.commandchangedcallback = cb

    def setupdowncallback(self, cb):
        self.updowncallback = cb

    def setcommandline(self, text):
        self.ce.setText(text)

    def __init__(self, pwin, css):
        super().__init__(pwin)
        self.pwin = pwin

        self._hadfocus = False

        self.setObjectName('ConsoleWindow')

        self.promptfirstset = True
        self.commandchangedcallback = None
        self.updowncallback = None

        self.ce = QtGui.QLineEdit(self)
        self.ce.setObjectName('CommandLine')
        self.ce.show()
        self.ce.textChanged.connect(lambda: self.commandchange_event())
        #self.ce.setEnabled(False)
        #self.ce._keyPressEvent = self.ce.keyPressEvent
        #self.ce.keyPressEvent = self.dummyKeyPressEvent

        self.wp = QtWebKit.QWebView(self)
        self.wp.move(3, 0)
        self.wp.keyPressEvent = self.keyPressEvent

        self.ce.returnPressed.connect(lambda: self._commandEvent())

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # hopefully this ends up calling resizeEvent
        self.wp.resize(600, 100)

        self.wp.setObjectName('ConsoleHTMLView')
        # style="font-size: 8pt; line-height: 1; font-family: consolas;"
        self.wp.setHtml(' \
            <html><head><style>%s</style></head><body> \
            <script language="javascript"> \
                function scrollcheck() { \
                    var scrollit; \
                    if (document.body.scrollHeight - document.body.scrollTop <= (document.body.clientHeight + 10)) \
                        return true; \
                    else \
                        return false; \
                } \
                function addline(line) { \
                    var scrollit = scrollcheck(); \
                    var m = document.createElement("div"); \
                    m.innerHTML = line; \
                    lines.appendChild(m); \
                    if (scrollit) \
                        window.scrollTo(0, document.body.scrollHeight); \
                } \
            </script> \
            <div class="lines" id="lines"></div><span class="xprompt" id="xprompt"></span></body></html>' 
        % css)

        self.wp.show()

        #self.wp.contentSizeChanged.connect(lambda: print('CHANGED'))

        #self.sa.setWidgetResizable(1)
        #self.sa.setWidget(self.wp)
        #self.sa.show()

        self.resize(600, 100)

        self.show()

        # used to handle terminal escape sequences
        self.colormap = {
            '0': 'black',
            '1': 'red',
            '2': 'green',
            '3': 'yellow',
            '4': 'blue',
            '5': 'magenta',
            '6': 'cyan',
            '7': 'white',
            '9': 'default',
        }

        self.fgbright = False
        self.nfgcolor = 'hc_fg_default'
        self.nbgcolor = 'hc_bg_default'
        self.fgcolor = self.nfgcolor
        self.bgcolor = self.nbgcolor

    def processline(self, line, fgdef = None, bgdef = None):
        """Add line but convert terminal codes into HTML and convert from bytes to string.
        """

        # convert to string and replace any crazy characters
        line = line.decode('utf8', 'ignore')

        line = line.replace('\\', '\\\\')

        # escape any quotes because we encode this string into
        # javascript call and unescaped quotes will screw it up
        line = line.replace('"', '\\"')

        # split it to handle terminal escape codes
        parts = line.split('\x1b')

        line = []

        fgdef = fgdef or self.fgcolor
        bgdef = bgdef or self.bgcolor

        line.append('<span class=\\"%s %s\\">%s</span>' % (fgdef, bgdef, parts[0].replace(' ', '&nbsp')))

        for x in range(1, len(parts)):
            part = parts[x]
            if part[0] == '#':
                hexcolor = part[1:part.find(';')]
                hexcolor = hexcolortotuple(hexcolor)
                hexcolor = hexcolordimblue(hexcolor, 0.4)
                #hexcolor = hexcolordimer(hexcolor, 1.0, 1.0, 0.6)
                hexcolor = tupletohexcolor(hexcolor)

                rmsg = part[part.find(';') + 1:]
                rmsg = rmsg.replace('   ', '&nbsp;' * 3)
                rmsg = rmsg.replace(' ', '&nbsp;')
                line.append('<span style=\\"color: #%s;\\">%s</span>' % (hexcolor, rmsg))
                #line.append(rmsg)
                continue
            if part[0] != '[':
                print('Expected [!')
            cstr = part[1:part.find('m')]
            rmsg = part[part.find('m') + 1:]
            codes = cstr.split(';')
            if len(cstr) < 1:
                self.fgcolor = self.nfgcolor
                self.bgcolor = self.nbgcolor
            for code in codes:
                if len(code) < 1:
                    continue
                if code == '0':
                    self.fgcolor = self.nfgcolor
                    self.bgcolor = self.nbgcolor
                    self.fgbright = False
                    continue
                if code == '1':
                    self.fgbright = True
                    continue
                if code == '2':
                    self.fgbright = False
                    continue
                if code[0] == '3':
                    val = code[1]
                    if val in self.colormap:
                        if self.fgbright:
                            self.fgcolor = 'hc_bfg_%s' % self.colormap[val]
                        else:
                            self.fgcolor = 'hc_fg_%s' % self.colormap[val]
                    continue
                if code[0] == '4':
                    if code[1] in self.colormap:
                        self.bgcolor = 'hc_bg_' % self.colormap[code[1]]
                    continue
                raise Exception('Ignored Code "%s"' % code)

            rmsg = rmsg.replace('\t', '&#9;')
            rmsg = rmsg.replace(' ', '&nbsp;')
            line.append('<span class=\\"%s %s\\">%s</span>' % (self.fgcolor, self.bgcolor, rmsg))

        line = ''.join(line)

        return line

    def processthenaddline(self, line):
        line = self.processline(line)
        if len(line) > 0:
            self.addline(line)

    def scrolltoend(self):
        self.wp.page().mainFrame().evaluateJavaScript('window.scrollTo(0, document.body.scrollHeight);')

    def setprompt(self, prompt, fgdef = None, bgdef = None):
        # set the prompt AND //commentedout//scroll the window buffer to end//
        prompt = self.processline(prompt, fgdef, bgdef)
        self.wp.page().mainFrame().evaluateJavaScript('var scrollit = scrollcheck(); xprompt.innerHTML = "%s"; if (scrollit) window.scrollTo(0, document.body.scrollHeight);' % prompt)
        if self.promptfirstset:
            self.scrolltoend()
            self.promptfirstset = False

    def addline(self, html):
        # add line to content with magic to make
        # it scroll ONLY if already scrolled near
        # to end of document (helps to lock it if
        # the user has it scrolled upwards when new
        # stuff is added)
        self.wp.page().mainFrame().evaluateJavaScript('addline("%s");' % html)
        return


