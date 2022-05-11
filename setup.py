from setuptools import setup

setup(name='newm',
      version='0.3',
      description='newm - Wayland compositor',
      url="https://github.com/jbuchermn/newm",
      author='Jonas Bucher',
      author_email='j.bucher.mn@gmail.com',
      packages=['newm', 'newm.helper', 'newm.resources', 'newm.overlay', 'newm.widget', 'newm.dbus', 'newm.gestures', 'newm.gestures.provider', 'newm_panel_basic'],
      package_data={'newm.resources': ['wallpaper.jpg']},
      scripts=['bin/start-newm', 'bin/.start-newm', 'bin/newm-cmd', 'bin/newm-panel-basic'],
      install_requires=[
          'pycairo',
          'psutil',
          'python-pam',
          'pyfiglet',
          'dasbus',
          'thefuzz'
      ])
