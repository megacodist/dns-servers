#
# 
#

import gettext
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from utils.settings import AppSettings
from utils.types import InvalidFileError


_APP_DIR = Path(__file__).resolve().parent
"""The root directory of the application."""

_settings: AppSettings

_RES_DIR = _APP_DIR / 'res'

# The translator object...
_trans = gettext.translation(
    domain='main',
    localedir=_APP_DIR / 'locales',
    languages=('en',))
"""The translator object."""
_trans.install()

if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


def main() -> None:
    global _RES_DIR
    global _settings
    from utils.logger import configureLogger
    # Configuring logger...
    print(_('CONFIG_LOGGER'))
    configureLogger(_APP_DIR / 'log.log')
    # Loading application settings...
    print(_('LOADING_SETTINGS'))
    try:
        _settings = AppSettings()
        _settings.Load(_APP_DIR / 'config.bin')
    except InvalidFileError:
        print(_('INVALID_SETTINGS_FILE'))
    # Loading database...
    from db.sqlite3 import SqliteDb
    db = SqliteDb(_APP_DIR / 'db.db3')
    # Creating the window...
    from widgets.dns_win import DnsWin
    try:
        dnsWin = DnsWin(
            _RES_DIR,
            _APP_DIR / 'LICENSE',
            _settings,
            db,)
        dnsWin.mainloop()
    finally:
        db.close()
        _settings.Save()


if __name__ == '__main__':
    main()
