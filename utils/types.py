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

import PIL.Image
import PIL.ImageTk


TkImg = PIL.ImageTk.PhotoImage
"""Tkinter compatible image type."""


class GifImage:
    """It is actually a list of `PIL.ImageTk.PhotoImage` to hold the
    GIF frames. The objects of this class support zero-based integer
    subscript notation for reading, not setting, GIF frames.
    """
    def __init__(self, gif: PathLike) -> None:
        from PIL import ImageSequence
        self._frames: list[TkImg] = []
        """The frames of this GIF image."""
        self._idx: int = 0
        """The index of the next frame."""
        self._HGIF_WAIT = PIL.Image.open(gif)
        for frame in ImageSequence.Iterator(self._HGIF_WAIT):
            frame = frame.convert("RGBA")
            self._frames.append(PIL.ImageTk.PhotoImage(frame))
    
    def nextFrame(self) -> TkImg:
        """Returns the next frame of this gif image. On consecutive
        calls, this methods endlessly loops over all available frames
        jumping from end to the first.
        """
        try:
            frame = self._frames[self._idx]
            self._idx += 1
        except IndexError:
            frame = self._frames[0]
            self._idx = 1
        return frame
    
    def close(self) -> None:
        """Releases the GIF file."""
        self._frames.clear()
        del self._frames
        self._HGIF_WAIT.close()
        del self._HGIF_WAIT
    
    def __getitem__(self, __idx: int, /) -> TkImg:
        return self._frames[__idx]
    
    def __del__(self) -> None:
        if hasattr(self, '_frames'):
            self._frames.clear()
            del self._frames
        if hasattr(self, '_HGIF_WAIT'):
            self._HGIF_WAIT.close()
            del self._HGIF_WAIT


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
        self._lock = RLock()
        self._file: PathLike

    def Load(self, file: PathLike) -> None:
        """Loads settings from the specified file into the singleton
        object.

        #### Exceptions:
        1. `InvalidFileError`: if content of the file cannot be
        interpreted as previously saved application settings.
        """
        # Getting hold of settings singleton object...
        count = 0
        while not self._lock.acquire(True, 0.25):
            sleep(0.25)
            count += 1
            if count > 16:
                logging.error(
                    'Could not getting hold of settings singleton object',
                    stack_info=True,)
                return
        # Reading settings from the file...
        self._file = file
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
            self._lock.release()

    def Save(self) -> None:
        """Saves settings to the last loaded file."""
        # Getting hold of settings singleton object...
        count = 0
        while not self._lock.acquire(True, 0.25):
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
            with open(self._file, mode='wb') as settingsFileStream:
                settingsFileStream.write(signature_)
                settingsFileStream.write(binSettings)
        finally:
            self._lock.release()

    def _GetClassAttrsName(self) -> tuple[str, ...]:
        """Returrns a tuple of all class attributes names."""
        return self._GetAttrsName(self.__class__)
    
    def _GetObjAttrsName(self) -> tuple[str, ...]:
        return self._GetAttrsName(self)

    def _GetAttrsName(self, obj: object) -> tuple[str, ...]:
        attrs = [
            attr for attr in dir(obj)
            if not callable(getattr(obj, attr)) and not attr.startswith('_')]
        attrs.sort()
        return tuple(attrs)
