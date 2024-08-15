#
# 
#

from dataclasses import dataclass
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, TYPE_CHECKING, Hashable, Iterable, NamedTuple, Sequence, TypeVar, overload

from tksheet import Sheet

from ntwrk import ACIdx, AdapCfgBag, NetAdap, NetConfig


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


class _InfoWinSettings:
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


class InfoWin(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            obj: Any,
            title_cb: Callable[[Any], str],
            attrs_cb: Callable[[Any], Iterable[str]],
            close_cb: Callable[[int], None],
            *,
            xy: tuple[int, int] | None = None,
            width: int = 400,
            height: int = 350,
            key_width: int = 150,
            value_width: int = 180,
            ) -> None:
        super().__init__(master)
        self.resizable(True, True)
        self.geometry(f'{width}x{height}')
        #
        self._obj = obj
        """The object its attributes to be shown."""
        self._cbTitle = title_cb
        """The callback which gives a suitable title back for the object."""
        self._cbAttrs = attrs_cb
        """The callback which gives attributes of the object."""
        self._cbClose = close_cb
        #
        self._sheet = Sheet(self, headers=[_('KEY'), _('VALUE'),])
        self._sheet.column_width(0, key_width)
        self._sheet.column_width(1, value_width)
        self._sheet.enable_bindings(
            'single_select',
            'drag_select',
            'column_select',
            'row_select',
            'column_width_resize',
            'double_click_column_resize',
            'up',
            'down',
            'left',
            'right',
            'prior', # page up
            'next',
            'copy',)
        self._sheet.pack(fill=tk.BOTH, expand=True)
        #
        self.settings = _InfoWinSettings(
            0,
            0,
            width,
            height,
            key_width,
            value_width)
        self.populateInfo()
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
        import re
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
            colsWidths = self._sheet.get_column_widths()
            self.settings = _InfoWinSettings(
                int(match.group('x')),
                int(match.group('y')),
                int(match.group('width')),
                int(match.group('height')),
                int(colsWidths[0]),
                int(colsWidths[1]),)
        else:
            logging.error(
                'Cannot get the geometry of the InfoWin.',
                stack_info=True)
        if self._cbClose:
            self._cbClose(self._obj)
        self.destroy()
    
    def _clear(self) -> None:
        count = len(self._sheet.get_sheet_data())
        for idx in reversed(range(count)):
            self._sheet.delete_row(idx)
    
    def populateInfo(self) -> None:
        from ntwrk import AbsNetItem
        self._clear()
        self.title(self._cbTitle(self._obj))
        for attr in self._cbAttrs(self._obj):
            self._sheet.insert_row([attr, getattr(self._obj, attr)])
    
    def showWin(self) -> None:
        """Shows the window."""
        self.focus_set()
    
    def showDialog(self) -> None:
        """Shows the window as dialog box."""
        self.grab_set()
        self.focus_set()
        self.wm_deiconify()
        self.wait_window()


_T = TypeVar('_T')
_Hashable = TypeVar('_Hashable', bound=Hashable)

class InfoWinMixin:
    @overload
    def __init__(
            self,
            title_cb: Callable[[_Hashable], str],
            attrs_cb: Callable[[_Hashable], Iterable[str]],
            ) -> None:
        """Initializes a new instance of this mixin. If the objects to see
        their attributes are hashable, and you don't need to specify a
        hash callback.
        """
        pass

    @overload
    def __init__(
            self,
            title_cb: Callable[[_T], str],
            attrs_cb: Callable[[_T], Iterable[str]],
            *,
            hash_cb: Callable[[_T], _Hashable] | None = None,
            ) -> None:
        """Initializes a new instance of this mixin. If the objects to see
        their attributes are NOT hashable, and you MUST specify a
        hash callback.
        """
        pass

    def __init__(
            self,
            title_cb: Callable[[_T], str],
            attrs_cb: Callable[[_T], Iterable[str]],
            sett_obj: Any | None = None,
            *,
            hash_cb: Callable[[_T], _Hashable] | None = None,
            ) -> None:
        """Initializes a new instance of this mixin.

        *`attrs_cb`: an attrs callback is necessary that provides the
        attributes of objects to be shown in info windows.
        * `hash_cb`: if your objects are hashable and you're sure that
        `hash` built-in function gives unique integer for all of them,
        then you don't have to specify the hash callback.
        """
        self._cbTitle = title_cb
        self._cbAttrs = attrs_cb
        self._cbHash = hash_cb
        self._infoWins = dict[int, InfoWin]()
    
    def _getObjHash(self, obj: _T) -> int:
        """Gets the unique hash for provided object."""
        temp = obj
        if self._cbHash is not None:
            temp = self._cbHash(obj) # type: ignore
        return hash(temp)
    
    def _grabInoWinSettings(self, info_win: InfoWin) -> None:
        """Grabs settings for a `InfoWin` to save into the
        `_settings` attribute.
        """
        nidSettings = info_win.settings
        self._settings.nid_x = nidSettings.x
        self._settings.nid_y = nidSettings.y
        self._settings.nid_width = nidSettings.width
        self._settings.nid_height = nidSettings.height
        self._settings.nid_key_width = nidSettings.key_width
        self._settings.nid_value_width = nidSettings.value_int
    
    def _onInfoWinClosed(self, obj: _T) -> None:
        pass
    
    def showInfoWin(self, obj: _T) -> None:
        hash_ = self._getObjHash(obj)
        try:
            infoWin = self._infoWins[hash_]
        except KeyError:
            infoWin = InfoWin(
                self, # type: ignore
                obj,
                self._cbTitle,
                self._cbAttrs,
                self._onInfoWinClosed,)
        else:
            infoWin.showWin()
    
    def closeInfoWin(self, obj: _T) -> None:
        hash_ = self._getObjHash(obj)
        try:
            infoWin = self._infoWins[hash_]
        except KeyError:
            pass
        else:
            infoWin.closeWin()
