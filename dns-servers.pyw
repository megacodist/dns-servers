#
# 
#

from pathlib import Path

from utils.settings import AppSettings
from utils.types import InvalidFileError


_APP_DIR = Path(__file__).resolve().parent
"""The root directory of the application."""

_settings: AppSettings

_RES_DIR = _APP_DIR / 'res'


def main() -> None:
    global _RES_DIR
    global _settings
    # Loading application settings...
    print('Loading settings...')
    try:
        _settings = AppSettings()
        _settings.Load(_APP_DIR / 'config.bin')
    except InvalidFileError:
        print('Invalid settings file, using defaults')
    # Loading database...
    from db.sqlite3 import SqliteDb
    db = SqliteDb(_APP_DIR / 'db.db3')
    # Creating the window...
    from widgets.dns_win import DnsWin
    try:
        print('Creating app window...')
        dnsWin = DnsWin(_RES_DIR, _settings, db)
        dnsWin.mainloop()
    finally:
        _settings.Save()


if __name__ == '__main__':
    main()
