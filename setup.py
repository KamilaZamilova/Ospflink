# setup py
from distutils.core import setup
from setuptools import find_packages
import  os, os.path
import shutil
import sys
from inspect import getsourcefile
dir  = os.path.abspath(os.curdir)

non_default = ['ospflink.cfg']

setup(name = 'ospflink',
    version = '1.1.RC1',
    packages = ['Scripts', 'Lib', 'Lib.site_packages', 'Lib.site_packages.ospflink','Lib.site_packages.data'],
    package_data = {'Lib.site_packages': ['data/*.dat', 'data/*.txt']},
    url = ['https://github.com/KamilaZamilova/Ospflink'],
    data_files = ['ospflink.default.cfg']
)

def Copy(non_default):
    for file in non_default:
        mfile = dir + '/' + file
        if not os.path.isfile(mfile) :
            open(mfile,"a").close()
            x = file.rfind('.')
            name = file[0:-(len(file) - x)]
            default_file = sys.argv[3] + '/' + name + '.default' + '.cfg'
            shutil.copy(default_file,mfile)
if (sys.argv[1] == 'install'):
    Copy(non_default)