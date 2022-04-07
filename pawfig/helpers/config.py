import os.path
import pathlib
import sys
from configparser import ConfigParser


class Config:
    _parser = ConfigParser()
    _config_file: pathlib.Path

    def __init__(self):
        if sys.platform == 'linux' and not os.path.exists('/etc/pawfiguration'):
            os.makedirs('/etc/pawfiguration')

            self._config_file = pathlib.PosixPath('/etc/pawfiguration/config.ini')
            if not self._config_file.exists():
                self._create_ini(self._config_file)

            self._parser.read(self._config_file)
            self.account = self._parser['Account']


    def _create_ini(self, path):
        with path.open(mode='w') as f:
           self._parser['Account'] = {}
           self._parser.write(f)


    def reload(self):
        self._parser.read(self._config_file)
        for section in self._parser.sections():
            setattr(self, section.lower(), self._parser[section])

