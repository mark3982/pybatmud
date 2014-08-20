import urllib.request
import urllib.error

def fetch(url):
    response = urllib.request.urlopen(url)
    # headers, info, getheaders
    #print(response.getheaders())
    return response.read()

def main():
    # https://www.bat.org/ci/barsoomian_male.png
    classes = (
        'barsoomian', 'brownie', 'catfolk', 'centaur', 'cromagnon', 'cyclops', 'demon',
        'doppelganger', 'draconian', 'drow', 'duck', 'duergar', 'dwarf', 'elf', 'ent',
        'gargoyle', 'giant', 'gnoll', 'gnome', 'hobbit', 'human', 'kobold', 'leech',
        'leprechaun', 'lich', 'lizardman', 'merfolk', 'minotaur', 'moomin', 'ogre',
        'orc', 'penguin', 'satyr', 'shadow', 'skeleton', 'sprite', 'thrikhren', 'tinmen',
        'titan', 'troll', 'valar', 'vampire', 'wolfman', 'zombie'
    )

    genders = ('male', 'female')

    for c in classes:
        for gender in genders:
            print('fetching', c, gender)
            imgdata = fetch('https://www.bat.org/ci/%s_%s.png' % (c, gender))
            fd = open('%s_%s.png' % (c, gender), 'wb')
            fd.write(imgdata)
            fd.close()


main()