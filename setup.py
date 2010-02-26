# script for py2exe
# run using following command: "python setup.py py2exe"

from distutils.core import setup
from glob import glob
import py2exe

data_files=[('Microsoft.VC90.CRT', ['msvcp90.dll', 'Microsoft.VC90.CRT.manifest']),
            ('images', glob('images\\*'))]

setup(
        windows=[{'script':'pyopenvpnman.py',
                  'icon_resources': [(1, 'images\\app32.ico')]}],
        data_files=data_files,
        options={'py2exe':{
                    'optimize': 1,
                    'bundle_files': 3}}
)
