from setuptools import setup

setup(name='newm',
      version='0.2',
      description='newm - Wayland compositor',
      url="https://github.com/jbuchermn/newm",
      author='Jonas Bucher',
      author_email='j.bucher.mn@gmail.com',
      packages=['newm', 'newm.resources', 'newm.overlay', 'newm.widget', 'newm_panel_basic'],
      package_data={'newm.resources': ['wallpaper.jpg']},
      scripts=['bin/start-newm', 'bin/.start-newm', 'bin/newm-cmd', 'bin/newm-panel-basic'],
      install_requires=[
          'pycairo',
          'psutil',
          'websockets',
          'python-pam',
          'pyfiglet',
          'fuzzywuzzy',
          'thefuzz'
      ])
