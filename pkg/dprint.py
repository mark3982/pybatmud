import os.path

if os.path.exists('dprint'):
    dprintenabled = True
else:
    dprintenabled = False

def dprint(fstr, *args):
    if not dprintenabled:
        return
    print('+' + fstr, *args)