#
# 
#

from pathlib import Path

from utils.settings import AppSettings
from utils.types import InvalidFileError


_APP_DIR = Path(__file__).resolve().parent
"""The root directory of the application."""

_SETTINGS: AppSettings

_RES_DIR = _APP_DIR / 'res'


def main() -> None:
    global _RES_DIR
    global _SETTINGS
    print('Loading settings...')
    try:
        _SETTINGS = AppSettings()
        _SETTINGS.Load(_APP_DIR / 'config.bin')
    except InvalidFileError:
        print('Invalid settings file, using defaults')
    from widgets.dns_win import DnsWin
    try:
        print('Creating app window...')
        dnsWin = DnsWin(_RES_DIR, _SETTINGS)
        dnsWin.mainloop()
    finally:
        pass


if __name__ == '__main__':
    main()
