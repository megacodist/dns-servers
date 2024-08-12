#
# 
#

from __future__ import annotations
import logging
from os import fspath, PathLike
import re
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, TYPE_CHECKING


if TYPE_CHECKING:
    _: Callable[[str], str]


class _LicWinSettings:
    @classmethod
    def checkObj(cls, sett_obj: Any) -> bool:
        """Checks whether the settings object has necessary attributes."""
        return all([
            hasattr(sett_obj, 'licw_x'),
            isinstance(getattr(sett_obj, 'licw_x'), int),
            hasattr(sett_obj, 'licw_y'),
            isinstance(getattr(sett_obj, 'licw_y'), int),
            hasattr(sett_obj, 'licw_width'),
            isinstance(getattr(sett_obj, 'licw_width'), int),
            hasattr(sett_obj, 'licw_height'),
            isinstance(getattr(sett_obj, 'licw_height'), int),])

    @classmethod
    def fromObj(cls, sett_obj: Any) -> _LicWinSettings:
        """Reads license window related settings from application settings
        object. Raises `TypeError` upon any inconsistency.
        """
        try:
            return _LicWinSettings(
                sett_obj.licw_x,
                sett_obj.licw_y,
                sett_obj.licw_width,
                sett_obj.licw_height)
        except AttributeError as err:
            raise TypeError(err.args)

    def __init__(
            self,
            x: int,
            y: int,
            width: int,
            height: int,
            ) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def save(self, sett_obj: Any) -> None:
        """Saves this object to the provided settings object (`sett_obj`).
        Raises `TypeError` upon any inconsistency.
        """
        origValues = dict[str, Any]()
        try:
            temp = sett_obj.licw_x
            sett_obj.licw_x = self.x
            origValues['licw_x'] = temp
            temp = sett_obj.licw_y
            sett_obj.licw_y = self.y
            origValues['licw_y'] = temp
            temp = sett_obj.licw_width
            sett_obj.licw_width = self.width
            origValues['licw_width'] = temp
            temp = sett_obj.licw_height
            sett_obj.licw_height = self.height
            origValues['licw_height'] = temp
        except (AttributeError, TypeError) as err:
            # Rolling back modifications to the `_settings`...
            for attr, value in origValues.items():
                setattr(sett_obj, attr, value)
            logging.error(
                'failed to save settings of license window to the '
                    'application settings object: %s',
                err)


class _LicenseWin(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            lic_file: str | PathLike,
            close_cb: Callable[[], None] | None = None,
            *,
            settings: _LicWinSettings | None = None,
            ) -> None:
        super().__init__(master)
        self.title(_('LICENSE'))
        self.resizable(True, True)
        self._cbClose = close_cb
        self.settings = settings
        # Initializing GUI...
        self._frm = ttk.Frame(self)
        self._frm.rowconfigure(0, weight=1)
        self._frm.columnconfigure(0, weight=1)
        self._frm.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._hscrllbr = ttk.Scrollbar(
            self._frm,
            orient='horizontal')
        self._vscrllbr = ttk.Scrollbar(
            self._frm,
            orient='vertical')
        self._txt = tk.Text(
            self._frm,
            wrap='none')
        self._hscrllbr.config(
            command=self._txt.xview)
        self._vscrllbr.config(
            command=self._txt.yview)
        self._txt.config(
            xscrollcommand=self._hscrllbr.set,
            yscrollcommand=self._vscrllbr.set)
        self._hscrllbr.grid(
            row=1,
            column=0,
            sticky=tk.NSEW)
        self._vscrllbr.grid(
            row=0,
            column=1,
            sticky=tk.NSEW)
        self._txt.grid(
            row=0,
            column=0,
            sticky=tk.NSEW)
        #
        self._szgrp = ttk.Sizegrip(self._frm)
        self._szgrp.grid(
            row=1,
            column=1,
            sticky=tk.NSEW,)
        #
        with open(fspath(lic_file), 'rt') as lcnsStream:
            self._txt.insert(
                tk.END,
                '\n'.join(lcnsStream.readlines()))
        self._txt.config(state=tk.DISABLED)
        #
        self._setGeometry()
        # Binding events...
        self.protocol('WM_DELETE_WINDOW', self.closeWin)
    
    def _setGeometry(self) -> None:
        if self.settings:
            self.geometry(
                f'{self.settings.width}x{self.settings.height}'
                f'+{self.settings.x}+{self.settings.y}')
        else:
            self.geometry('400x300')
            self.after(10, self._centerDialog, self.master)
    
    def _centerDialog(self, parent: tk.Misc) -> None:
        _, x, y = parent.winfo_geometry().split('+')
        x = int(x) + (parent.winfo_width() - self.winfo_width()) // 2
        y = int(y) + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')

    def closeWin(self) -> None:
        # Getting the geometry of the License Dialog (LD)...
        w_h_x_y = self.winfo_geometry()
        GEOMETRY_REGEX = r"""
            (?P<width>\d+)    # The width of the window
            x(?P<height>\d+)  # The height of the window
            \+(?P<x>\d+)      # The x-coordinate of the window
            \+(?P<y>\d+)      # The y-coordinate of the window"""
        match = re.search(
            GEOMETRY_REGEX,
            w_h_x_y,
            re.VERBOSE)
        if match:
            self.settings = _LicWinSettings(
                int(match.group('x')),
                int(match.group('y')),
                int(match.group('width')),
                int(match.group('height')),)
        else:
            logging.error('Cannot get the geometry of License Dialog.')
        #
        if self._cbClose:
            self._cbClose()
        self.destroy()
    
    def showWin(self) -> None:
        self.focus_set()
    
    def showDialog(self) -> None:
        """Shows the window as dialog box."""
        self.grab_set()
        self.focus_set()
        self.wm_deiconify()
        self.wait_window()


class LicWinMixin:
    """This class encapsulates license window and all its API. You must
    put it in the inheritance list of your app window, like the following:

    `class SomeWin(tkinter.Tk, LicWinMixin):`

    and initializing it like this:

    `LicWinMixin.__init__(self, lic_file, settings)`

    * `lic_file`: a `PathLike` object pointing to the license file in the
    file system.
    * `settings_obj`: the optional application settings object that is
    supposed to have `licw_x: int`, `licw_y: int`, `licw_width: int`, and
    `licw_height: int` attributes.

    #### API
    In the derived class, the following methods will be available:
    * `self.showLicWin()`
    * `self.closeLicWin()`
    """
    def __init__(
            self,
            lic_file: PathLike,
            sett_obj: Any | None = None,
            ) -> None:
        """* `lic_file`: a `PathLike` object pointing to the license file in the
        file system.
        * `settings_obj`: the optional application settings object that is
        supposed to have `licw_x: int`, `licw_y: int`, `licw_width: int`, and
        `licw_height: int` attributes.
        """
        self._licWin: _LicenseWin | None = None
        self._LIC_FILE = lic_file
        self._appSettings = sett_obj if sett_obj is not None and \
            _LicWinSettings.checkObj(sett_obj) else None

    def showLicWin(self) -> None:
        if self._licWin is None:
            settings = _LicWinSettings.fromObj(self._appSettings) if \
                self._appSettings is not None else None
            self._licWin = _LicenseWin(
                self, # type: ignore
                lic_file=self._LIC_FILE,
                close_cb=self._onLicWinClosed,
                settings=settings,)
        self._licWin.showWin()
    
    def closeLicWin(self) -> None:
        """Closes the license window. If it is already closed, it does
        nothing.
        """
        if self._licWin is not None:
            self._licWin.closeWin()
    
    def _onLicWinClosed(self) -> None:
        try:
            self._licWin.settings.save(self._appSettings) # type: ignore
        except TypeError as err:
            logging.error(
                'failed to save license window settings to the aplication '
                    'settings object: %s',
                err)
        self._licWin = None
