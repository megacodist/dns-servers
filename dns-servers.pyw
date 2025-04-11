#
# 
#

# Checking the system -------------------------------------
from pathlib import Path
import platform
import subprocess
import sys
from typing import TYPE_CHECKING, Callable
# Creating the spinner object...
from utils.spinner import Spinner, SpinnerStyle
spinner = Spinner(SpinnerStyle.BLOCK)
"""The spinner object to ensute the user of background tasks on the
terminal.
"""
# Getting application dir...
_APP_DIR = Path(__file__).resolve().parent
"""The root directory of the application."""
# The translator function...
import gettext
_trans = gettext.translation(
    domain='main',
    localedir=_APP_DIR / 'locales',
    languages=('en',))
"""The translator function. It translates every string ID to its
translation.
"""
_trans.install()
if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a
# Check the OS...
spinner.start(_("CHECKING_OS"))
if platform.system() != "Windows":
    spinner.stop(_("OS_INCOMPATIBILITY"))
    sys.exit(1)
spinner.stop(_("OS_APPROVED"))
# Check Python version...
spinner.start(_('CHECKING_PYTHON'))
if not ((3, 12,) <= sys.version_info < (4, 0,)):
    spinner.stop(_("PYTHON_INCOMPATIBILITY"))
    sys.exit(1)
spinner.stop(_("PYTHON_APPROVED"))
# Check requirements...
spinner.start(_('CHECKING_REQUIREMENTS'))
requirementsFile = _APP_DIR / "requirements.txt"
if not requirementsFile.exists():
    spinner.stop(_("REQUIREMENTS_FILE_NOT_FOUND"))
    sys.exit(1)
try:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "show", str(requirementsFile)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    spinner.stop(_("REQUIREMENTS_APPROVED"))
except subprocess.CalledProcessError:
    spinner.stop(_("REQUIREMENTS_NOT_INSTALLED"))
    spinner.start(_("INSTALLING_REQUIREMENTS"))
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirementsFile)])
        spinner.stop(_("REQUIREMENTS_INSTALLED"))
    except subprocess.CalledProcessError as err:
        spinner.stop(_("REQUIREMENTS_INSTALLATION_FAILED"))
        print(err)
        sys.exit(1)


# Running the application ---------------------------------
from utils.types import InvalidFileError

_RES_DIR = _APP_DIR / 'res'


def main() -> None:
    # Declaring variables ----------------------
    global _RES_DIR
    global _settings
    spinner = Spinner(SpinnerStyle.BLOCK)
    # Performing jobs ---------------------------
    # Configuring logger...
    spinner.start(_('CONFIG_LOGGER'))
    from utils.logger import configureLogger
    configureLogger(_APP_DIR / 'log.log')
    spinner.stop(_("LOGGER_CONFIGED"))
    # Loading application settings...
    spinner.start(_('LOADING_SETTINGS'))
    from utils.settings import AppSettings
    _settings = AppSettings()
    try:
        _settings.Load(_APP_DIR / 'config.bin')
    except InvalidFileError:
        print(_('BAD_SETTINGS_FILE'))
    spinner.stop(_("SETTINGS_LOADED"))
    # Loading database...
    spinner.start(_('LOADING_DB'))
    from db.sqlite3 import SqliteDb
    db = SqliteDb(_APP_DIR / 'db.db3')
    spinner.stop(_("DB_LOADED"))
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
