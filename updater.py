import urllib.request
import urllib.error
import os.path
import hashlib
import sys
import shutil
import zipfile
import time

from PyQt4 import QtGui
from PyQt4 import QtCore

class QLocalApplication(QtGui.QApplication):
    """Helps fix problem of main needing to catch notify event.
    """
    def __init__(self, argv):
        super().__init__(argv)
        self._notify = None             # the notification callback for redirection
        self.notifysuper = False        # would be False in standalone (see main.py)

    def notify(self, receiver, event):
        if self._notify is not None:
            # redirect to callback
            ret = self._notify(self, receiver, event)
            # callback did not handle anything?
            if ret is not None:
                return ret
        # call our super method
        return super().notify(receiver, event)

def fetch(url):
    try:
        response = urllib.request.urlopen(url)
        # headers, info, getheaders
        #print(response.getheaders())
        return response.read()
    except:
        pass
    return None

class QUpdateWindow(QtGui.QWidget):
    def __init__(self, current_tag, tags, userbase, app):
        super().__init__()

        self.app = app
        self.userbase = userbase
        self.tags = tags
        self.current_tag = current_tag

        sa = QtGui.QScrollArea(self)
        self.sa = sa

        #sa.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        sa.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.su = QtGui.QWidget(self)
        sa.setWidget(self.su)

        l = QtGui.QLabel(self.su)
        l.setText('Select And Click To Launch')
        l.show()

        h = 20
        cy = 20
        for x in range(0, len(tags)):
            tag = tags[x]
            self.make(cy, h, tag, current_tag)

            cy = cy + h + 1
        self.su.resize(280, cy)

        self.setFixedSize(300, 300)
        self.show()
    def mr(self, event, w):
        if True:
            # create cache directory
            tag = w.tag
            # clear install directory
            installdir = '%s/client' % self.userbase
            print('installdir', installdir)
            if os.path.exists(installdir):
                shutil.rmtree(installdir)
            # download the package..
            zipball_url = tag['zipball_url']
            # see if we already have the zip ball
            if not os.path.exists('./githubcache/%s.zip' % tag['name']):
                # download the zipball
                print('downloading zipball...')
                zipball = fetch(zipball_url)
                fd = open('./githubcache/%s.zip' % tag['name'], 'wb')
                fd.write(zipball)
                fd.close()
            # install the package..
            zf = zipfile.ZipFile('./githubcache/%s.zip' % tag['name'])
            zf.extractall('./temp')
            node = os.listdir('./temp')[0]
            shutil.move('./temp/%s' % node, './client')
            shutil.rmtree('./temp')
            #QtGui.QApplication.quit()

        os.chdir(self.userbase + '/client')
        # add path to python system then import main module
        # and execute it, hopefully, all works fine
        sys.path.append(self.userbase + '/client')

        import main

        self.app._notify = main.QLocalApplication.notify

        main.main()

        self.hide()
        self.setParent(None)

    def make(self, cy, h, tag, current_tag):
        tagname = tag['name']
        tagparts = tagname.split('-')
        tagparts = tagparts[0].split('.') + [tagparts[1]]

        # make sure our updater supports the tag
        if tagparts[-1] != 'blue':
            return

        xtype = tagparts[-2][-1] 

        if xtype == 'b':
            tagtype = 'BETA'
            pcolor = QtGui.QColor(66, 66, 0, 66)
        elif xtype == 'a':
            tagtype = 'ALPHA'
            pcolor = QtGui.QColor(66, 0, 0, 66)
        elif xtype == 'c':
            tagtype = 'RELEASE CANIDATE'
            pcolor = QtGui.QColor(0, 0, 66, 66)
        elif xtype == 'r':
            tagtype = 'RELEASE'
            pcolor = QtGui.QColor(99, 255, 99, 255)
        else:
            return
        l = QtGui.QLabel(self.su)
        pal = l.palette()
        pal.setColor(l.backgroundRole(), pcolor)
        l.setAutoFillBackground(True)
        l.setPalette(pal)
        l.enterEvent = lambda event: self.ee(event, l)
        l.leaveEvent = lambda event: self.le(event, l)
        l.mouseReleaseEvent = lambda event: self.mr(event, l)
        l.move(0, cy)
        l.resize(300, h)
        l.setStyleSheet('font-size: 12pt; font-family: monospace; background-color: %s;' % pcolor)
        if current_tag == tag['name']:
            l.setText('Version: %s Type: %s (INSTALLED)' % (tag['name'], tagtype))
        else:
            l.setText('Version: %s Type: %s' % (tag['name'], tagtype))
        l.raise_()
        l.show()
        l.tag = tag

    def le(self, event, w):
        pal = w.palette()
        pal.setColor(w.backgroundRole(), w.oldbgcolor)
        w.setAutoFillBackground(True)
        w.setPalette(pal)

    def ee(self, event, w):
        pal = w.palette()
        o = pal.color(w.backgroundRole())
        w.oldbgcolor = o
        pal.setColor(w.backgroundRole(), o.lighter(256))
        w.setAutoFillBackground(True)
        w.setPalette(pal)

    def resizeEvent(self, event):
        self.sa.resize(self.width(), self.height())

def update(userbase):
    # use cache if exists
    if not os.path.exists('./githubcache'):
        os.makedirs('./githubcache')
    tags = None
    if os.path.exists('./githubcache/tags_cache'):
        print('reading tags cache')
        fd = open('./githubcache/tags_cache', 'r')
        tags = eval(fd.read())
        fd.close()
        cachetime = tags['cachetime']
        tags = tags['tags']
        # every 10 minutes should be okay for now..
        if time.time() - cachetime > 60 * 10:
            print('force fetch')
            # force fetch
            tags = None
    fetched = False
    if tags is None:
        print('fetching tags..')
        fetched = True
        tags = fetch('https://api.github.com/repos/kmcguire3413/pybatmud/tags')
    if fetched:
        # write cache
        fd = open('./githubcache/tags_cache', 'w')
        fd.write('%s' % {'tags': tags, 'cachetime': time.time()})
        fd.close()

    if tags is None:
        print('can not download')
        return False
    tags = eval(tags)

    #for tag in tags:
        #print(tag['commit']['sha'], tag['name'])
        #zipball_url = tag['zipball_url']
        #zipball = fetch(zipball_url)
        #print(len(zipball))

    app = QLocalApplication(sys.argv)
    style = QtGui.QStyleFactory.create('Plastique')
    app.setStyle(style)

    if os.path.exists('%s/current_tag' % userbase):
        fd = open('%s/current_tag' % userbase, 'r')
        current_tag = fd.read()
        fd.close()
    else:
        current_tag = None

    w = QUpdateWindow(current_tag, tags, userbase, app)

    app.exec_()

def main():
    userbase = os.path.expanduser('~') + '/pybatmud'
    if not os.path.exists(userbase):
        os.makedirs(userbase)

    os.chdir(userbase)

    update(userbase)

main()