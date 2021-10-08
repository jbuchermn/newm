from setuptools import setup

setup(name='newm',
      version='0.1.0',
      description='pywm reference implementation',
      url="https://github.com/jbuchermn/newm",
      author='Jonas Bucher',
      author_email='j.bucher.mn@gmail.com',
      packages=['newm', 'newm.resources', 'newm.overlay', 'newm.widget', 'newm_panel_basic'],
      package_data={'newm.resources': ['wallpaper.jpg']},
      scripts=['start-newm', 'newm-cmd', 'newm-panel-basic'],
      install_requires=[
          'pycairo',
          'psutil',
          'websockets',
          'python-pam',
          'pyfiglet',
          'fuzzywuzzy'
      ])
