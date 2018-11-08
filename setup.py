import glob
import shutil
from distutils.core import setup

so = None
for f in glob.glob('build/_pywm.*.so'):
    so = f

if so is None:
    print("Could not find shared library")
    exit(1)

shutil.copy(so, 'pywm/_pywm.so')

setup(name='pywm',
      version='0.0.1',
      description='wlroots compositor with Python frontend',
      author='Jonas Bucher',
      author_email='j.bucher.mn@gmail.com',
      package_data={'pywm': ['_pywm.so']},
      packages=['pywm'])
