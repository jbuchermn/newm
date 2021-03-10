from setuptools import setup

setup(name='newm',
      version='0.0.9',
      description='pywm reference implementation',
      url="https://github.com/jbuchermn/newm",
      author='Jonas Bucher',
      author_email='j.bucher.mn@gmail.com',
      packages=['newm', 'newm.overlay', 'newm.widget'],
      scripts=['start-newm', 'newm-cmd'],
      install_requires=[
          'pycairo',
          'psutil',
          'websockets',
          'python-pam'
      ])
