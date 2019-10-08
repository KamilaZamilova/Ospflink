# setup py
from distutils.core import setup
import global_var
import  os, os.path
import shutil
import sys

from inspect import getsourcefile
dir  = os.path.abspath(os.curdir)

non_default = ['ospflink.cfg']

setup(name = 'ospflink',
    version = '1.1.RC1',
    py_modules = ['global_var'],
    packages = ['ospflink','data'],
    scripts = ['ospflink.py'],
    url = ['https://github.com/KamilaZamilova/Ospflink'],
    data_files = ['data/dummy.txt','ospflink.default.cfg']
)

def Copy(non_default):
    for file in non_default:
        mfile = sys.argv[3] + '/' + file
        if not os.path.isfile(mfile) :
            open(mfile,"a").close()
            x = file.rfind('.')
            name = file[0:-(len(file) - x)]
            default_file = dir + '/' + name + '.default' + '.cfg'
            shutil.copy(default_file,mfile)

Copy(non_default)