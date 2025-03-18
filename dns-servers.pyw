#
# 
#

import gettext
import sys
import platform
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
    # Declaraing variables ----------------------
    from utils.spinner import Spinner, SpinnerStyle
    global _RES_DIR
    global _settings
    spinner = Spinner(SpinnerStyle.BOUNCING_BALL)
    # Performing jobs ---------------------------
    # Check OS...
    spinner.start(_('CHECKING_OS'))
    if platform.system() != "Windows":
        print(_("OS_INCOMPATIBILITY"))
        sys.exit(1)
    # Check Python version...
    if sys.version_info < (3, 12):
        print(_("This application requires Python 3.12 or higher."))
        sys.exit(1)
    # Configuring logger...
    spinner.start(_('CONFIG_LOGGER'))
    from utils.logger import configureLogger
    configureLogger(_APP_DIR / 'log.log')
    spinner.stop()
    # Loading application settings...
    spinner.start(_('LOADING_SETTINGS'))
    try:
        _settings = AppSettings()
        _settings.Load(_APP_DIR / 'config.bin')
    except InvalidFileError:
        print(_('INVALID_SETTINGS_FILE'))
    spinner.stop()
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
