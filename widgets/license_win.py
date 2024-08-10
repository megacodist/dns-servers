#
# 
#

from dataclasses import dataclass
import logging
from os import fspath, PathLike
import re
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, TYPE_CHECKING


if TYPE_CHECKING:
    _: Callable[[str], str]


@dataclass
class _LicenseWinSettings:
    x: int
    y: int
    width: int
    height: int


class _LicenseWin(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            lic_file: str | PathLike,
            close_cb: Callable[[], None] | None = None,
            *,
            xy: tuple[int, int] | None = None,
            width: int = 400,
            height: int = 350,
            ) -> None:
        super().__init__(master)
        self.title(_('LICENSE'))
        self.resizable(True, True)
        self.geometry(f'{width}x{height}')
        self._cbClose = close_cb
        self.settings = _LicenseWinSettings(
            0 if xy is None else xy[0],
            0 if xy is None else xy[1],
            width,
            height,)
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
        with open(fspath(lic_file), 'rt') as lcnsStream:
            self._txt.insert(
                tk.END,
                '\n'.join(lcnsStream.readlines()))
        self._txt.config(state=tk.DISABLED)
        #
        if xy is None:
            self.after(10, self._centerDialog, master)
        else:
            self.geometry(f'+{xy[0]}+{xy[1]}')
        # Binding events...
        self.protocol('WM_DELETE_WINDOW', self.closeWin)
    
    def _centerDialog(self, parent: tk.Misc) -> None:
        _, x, y = parent.winfo_geometry().split('+')
        x = int(x) + (parent.winfo_width() - self.winfo_width()) // 2
        y = int(y) + (parent.winfo_height() - self.winfo_height()) // 2
        self.settings.x = x
        self.settings.y = y
        self.geometry(f'+{x}+{y}')

    def closeWin(self) -> None:
        settings = {}

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
            self.settings.width = int(match.group('width'))
            self.settings.height = int(match.group('height'))
            self.settings.x = int(match.group('x'))
            self.settings.y = int(match.group('y'))
        else:
            logging.error('Cannot get the geometry of License Dialog.')
        #
        if self._cbClose:
            self._cbClose()
        self.destroy()
    
    def showWin(self) -> None:
        self.focus_set()


class LicWinMixin:
    """This class encapsulates license window and all its API. You must
    put it in the inheritance list of your app window, like the following:

    `class SomeWin(tkinter.Tk, LicWinMixin):`

    and initializing it like this:

    `LicWinMixin.__init__(self, lic_file, settings)`

    * `lic_file`: a `PathLike` object pointing to the license file
    * `settings`: an object that must have `licw_x`, `licw_y`, `licw_width`,
    and `licw_height` attributes.
    """
    def __init__(
            self,
            lic_file: PathLike,
            settings: Any,
            ) -> None:
        self._licWin: _LicenseWin | None = None
        self._LIC_FILE = lic_file
        self._settings = settings

    def showLicWin(self) -> None:
        if self._licWin is None:
            try:
                xy = (self._settings.licw_x, self._settings.licw_y)
            except AttributeError as err:
                xy = None
                logging.error(
                    'failed to read XY coordinates of license window: %s',
                    err)
            try:
                width = self._settings.licw_width
            except AttributeError as err:
                width = 400
                logging.error(
                    'failed to read the width of license window: %s',
                    err)
            try:
                height = self._settings.licw_height
            except AttributeError as err:
                height = 300
                logging.error(
                    'failed to read the height of license window: %s',
                    err)
            self._licWin = _LicenseWin(
                self, # type: ignore
                lic_file=self._LIC_FILE,
                close_cb=self._onLicWinClosed,
                xy=xy,
                width=width,
                height=height,)
        self._licWin.showWin()
    
    def closeLicWin(self) -> None:
        """Closes the license window. If it is already closed, it does
        nothing.
        """
        if self._licWin is not None:
            self._licWin.closeWin()
    
    def _onLicWinClosed(self) -> None:
        origValues = dict[str, Any]()
        licWinSettings = self._licWin.settings # type: ignore
        try:
            origValues['licw_x'] = self._settings.licw_x
            self._settings.licw_x = licWinSettings.x
            origValues['licw_y'] = self._settings.licw_y
            self._settings.licw_y = licWinSettings.y
            origValues['licw_width'] = self._settings.licw_width
            self._settings.licw_width = licWinSettings.width
            origValues['licw_height'] = self._settings.licw_height
            self._settings.licw_height = licWinSettings.height
        except AttributeError as err:
            # Rolling back modifications to the `_settings`...
            try:
                self._settings
            except AttributeError:
                pass
            else:
                for attr, value in origValues.items():
                    setattr(self._settings, attr, value)
            logging.error(
                'failed to save settings of license window: %s',
                err)
        self._licWin = None
