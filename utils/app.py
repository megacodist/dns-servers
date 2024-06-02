#
# 
#

import base64
import hashlib
import hmac
import logging
from os import PathLike
import pickle
from threading import RLock
from time import sleep
from typing import Any


class InvalidFileError(Exception):
    """This error will be raised if the content of the specified file
    cannot be interpreted as previously saved application settings.
    """
    pass


class SingletonMeta(type):
    """Apply this meta clss to any class that you want to be singleton
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class AppSettings(object, metaclass=SingletonMeta):
    """Encapsulates APIs for persistence settings between different sessions
    of the application. This class offers a thread-safe singleton object which
    must typically be used as follow:

    1. Subclas from this class sand add default values for your app settings
    as class attributes.
    2. Call `AppSettings().Load('path/to/the/file')` to load settings from
    the specified file.
    3. Access attributes at the object level. Apart from giving access to
    saved settings, it also falls back to default settings at class level.
    4. Update attributes you want at object level.
    5. Call `AppSettings().Save()` to save settings to the file.
    """

    def __init__(self) -> None:
        self.lock = RLock()
        self.file: PathLike

    def Load(self, file: PathLike) -> None:
        """Loads settings from the specified file into the singleton
        object.

        #### Exceptions:
        1. `InvalidFileError`: if content of the file cannot be
        interpreted as previously saved application settings.
        """
        # Getting hold of settings singleton object...
        count = 0
        while not self.lock.acquire(True, 0.25):
            sleep(0.25)
            count += 1
            if count > 16:
                logging.error(
                    'Could not getting hold of settings singleton object',
                    stack_info=True,)
                return
        # Reading settings from the file...
        self.file = file
        try:
            settingsFileStream = open(
                file,
                mode='rb')
        except Exception as err:
            # An error occurred reading the settings file
            # Leaving settings dictionary empty...
            logging.error('Loading settings file failed', exc_info=True)
            raise err
        else:
            # Checking the signature...
            try:
                raw_settings = settingsFileStream.read()
                signature_ = hmac.digest(
                    key=b'a-secret-key',
                    msg=raw_settings[44:],
                    digest=hashlib.sha256)
                signature_ = base64.b64encode(signature_)
                isOk = hmac.compare_digest(
                    raw_settings[:44],
                    signature_)
                if isOk:
                    raw_settings = base64.b64decode(raw_settings[44:])
                    settings: dict[str, Any] = pickle.loads(raw_settings)
                else:
                    raise InvalidFileError()
                if not set(settings.keys()).issubset(
                        self._GetClassAttrsName()):
                    raise InvalidFileError()
            except Exception:
                # An error occurred checking signature of the settings file
                # Leaving settings dictionary empty...
                raise InvalidFileError()
            else:
                for attr in settings:
                    setattr(self, attr, settings[attr])
            finally:
                settingsFileStream.close()
        finally:
            self.lock.release()

    def Save(self) -> None:
        """Saves settings to the last loaded file."""
        # Getting hold of settings singleton object...
        count = 0
        while not self.lock.acquire(True, 0.25):
            sleep(0.25)
            count += 1
            if count > 16:
                logging.error(
                    'Could not getting hold of settings singleton object')
                return
        try:
            settings: dict[str, Any] = {}
            for attr in self._GetObjAttrsName():
                settings[attr] = getattr(self, attr)
            # Turning 'settings' to bytes (pickling)...
            binSettings = pickle.dumps(settings)
            binSettings = base64.b64encode(binSettings)
            # Signing the settings...
            # signature_ will be 64 bytes long...
            signature_ = hmac.digest(
                key=b'a-secret-key',
                msg=binSettings,
                digest=hashlib.sha256)
            # signature_ will be 86 bytes long...
            signature_ = base64.b64encode(signature_)
            # Writing settings to the file...
            with open(self.file, mode='wb') as settingsFileStream:
                settingsFileStream.write(signature_)
                settingsFileStream.write(binSettings)
        finally:
            self.lock.release()

    def _GetClassAttrsName(self) -> tuple[str, ...]:
        """Returrns a tuple of all class attributes names."""
        return self._GetAttrsName(self.__class__)
    
    def _GetObjAttrsName(self) -> tuple[str, ...]:
        return self._GetAttrsName(self)

    def _GetAttrsName(self, obj: object) -> tuple[str, ...]:
        attrs = [
            attr for attr in dir(obj)
            if not callable(getattr(self.__class__, attr)) and \
                attr[:2] != '__' and attr[-2:] != '__']
        attrs.sort()
        return tuple(attrs)
