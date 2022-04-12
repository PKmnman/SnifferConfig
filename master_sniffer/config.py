import os.path
import pathlib
from configparser import ConfigParser
from typing import Optional


class Config:
    _parser = ConfigParser()
    _config_file: pathlib.Path

    def __init__(self):
        os.makedirs('/etc/pawfiguration', exist_ok=True)

        self._config_file = pathlib.PosixPath('/etc/pawfiguration/config.ini')
        if not self._config_file.exists():
            self._create_ini(self._config_file)

        self._parser.read(self._config_file)
        self._account = self._parser['Account']

    def _create_ini(self, path):
        with path.open(mode='w') as f:
           self._parser['Account'] = {}
           self._parser.write(f)

    @property
    def credentials(self):
        """Retrieves the user api credentials from the config file."""
        if self._account is None:
            return None, None
        username = self._account.get('username')
        # This is unsecure but fine for the time being
        token = self._account.get('access_token')
        return (username, token)

    @credentials.setter
    def credentials(self, cred: tuple[Optional[str], Optional[str]]):
        changed = False
        if cred[0] is not None:
            self._parser.set('Account', 'username', cred[0])
            changed = True
        if cred[1] is not None:
            self._parser.set('Account', 'token', cred[1])
            changed = True
        if changed:
            self.save()

    def save(self):
        with self._config_file.open(mode='w') as f:
            self._parser.write(f)

    def reload(self):
        self._parser.read(self._config_file)
        for section in self._parser.sections():
            setattr(self, section.lower(), self._parser[section])
