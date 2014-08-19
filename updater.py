import urllib.request
import urllib.error
import os.path
import hashlib
import sys

def fetch(url):
    response = urllib.request.urlopen(url)
    # headers, info, getheaders
    #print(response.getheaders())
    return response.read()

def update(userbase):
    print('fetching master index..')
    # fetch master index file
    repo = 'http://kmcg3413.net/pybatmud/latest-stable'
    try:
        rindex = eval(fetch('%s/index' % repo))
    except urllib.error.HTTPError as e:
        print(e)
        print('During the update check the error above occured!')
        return

    # cycle through components of remote master index file
    for rel in rindex:
        rhash = rindex[rel]
        lpath = '%s/%s' % (userbase, rel)
        if os.path.exists(lpath):
            fd = open(lpath, 'rb')
            m = hashlib.sha512()
            m.update(fd.read())
            fd.close()
            lhash = m.digest()
        else:
            lhash = None
        if lhash != rhash:
            # update local file
            print('bad.. %s...%s...%s' % (rel, rhash[0:10], lhash[0:10]))
            tmp = lpath[0:lpath.rfind('/')]
            if not os.path.exists(tmp):
                os.makedirs(tmp)
            print('%s/%s' % (repo, rel))
            data = fetch('%s/%s_' % (repo, rel))
            fd = open(lpath, 'wb')
            fd.write(data)
            fd.close()
        else:
            print('good.. %s' % rel)

    # delete anything not included in the remote master index, if
    # you are a developer you should not be running this updater
    # and instead should be doing manual updates
    a = [userbase]
    b = []
    while len(a) > 0:
        for dirpath in a:
            nodes = os.listdir(dirpath)
            relpath = dirpath[len(userbase) + 1:]

            for node in nodes:
                filepath = '%s/%s' % (dirpath, node)
                if os.path.isdir(filepath):
                    b.append(filepath)
                    continue
                filerel = '%s/%s' % (relpath, node)
                if filerel[0] == '/':
                    filerel = filerel[1:]
                if filerel not in rindex:
                    os.remove(filepath)
        a = b
        b = []

def main():
    userbase = os.path.expanduser('~') + '/pybatmud/client'
    if not os.path.exists(userbase):
        os.makedirs(userbase)

    if len(sys.argv) < 2:
        update(userbase)
    # add path to python system then import main module
    # and execute it, hopefully, all works fine
    sys.path.append(userbase)
    import main
    os.chdir(userbase)
    main.main()

main()