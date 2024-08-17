#
# 
#

from __future__ import annotations
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
            hasattr(sett_obj, 'infow_x'),
            isinstance(getattr(sett_obj, 'infow_x'), int),
            hasattr(sett_obj, 'infow_y'),
            isinstance(getattr(sett_obj, 'infow_y'), int),
            hasattr(sett_obj, 'infow_width'),
            isinstance(getattr(sett_obj, 'infow_width'), int),
            hasattr(sett_obj, 'infow_height'),
            isinstance(getattr(sett_obj, 'infow_height'), int),
            hasattr(sett_obj, 'infow_key_width'),
            isinstance(getattr(sett_obj, 'infow_key_width'), int),
            hasattr(sett_obj, 'infow_value_width'),
            isinstance(getattr(sett_obj, 'infow_value_width'), int),])

    @classmethod
    def fromObj(cls, sett_obj: Any) -> _InfoWinSettings:
        """Reads license window related settings from application settings
        object. Raises `TypeError` upon any inconsistency.
        """
        try:
            return _InfoWinSettings(
                sett_obj.infow_x,
                sett_obj.infow_y,
                sett_obj.infow_width,
                sett_obj.infow_height,
                sett_obj.infow_key_width,
                sett_obj.infow_value_width,)
        except AttributeError as err:
            raise TypeError(err.args)

    def __init__(
            self,
            x: int,
            y: int,
            width: int,
            height: int,
            key_width: int,
            value_width: int,
            ) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.keyWidth = key_width
        self.valueWidth = value_width
    
    def save(self, sett_obj: Any) -> None:
        """Saves this object to the provided settings object (`sett_obj`).
        Raises `TypeError` upon any inconsistency.
        """
        origValues = dict[str, Any]()
        try:
            temp = sett_obj.infow_x
            sett_obj.infow_x = self.x
            origValues['infow_x'] = temp
            temp = sett_obj.infow_y
            sett_obj.infow_y = self.y
            origValues['infow_y'] = temp
            temp = sett_obj.infow_width
            sett_obj.infow_width = self.width
            origValues['infow_width'] = temp
            temp = sett_obj.infow_height
            sett_obj.infow_height = self.height
            origValues['infow_height'] = temp
            temp = sett_obj.infow_key_width
            sett_obj.infow_key_width = self.keyWidth
            origValues['infow_key_width'] = temp
            temp = sett_obj.infow_value_width
            sett_obj.infow_value_width = self.valueWidth
            origValues['infow_value_width'] = temp
        except (AttributeError, TypeError) as err:
            # Rolling back modifications to the `_settings`...
            for attr, value in origValues.items():
                setattr(sett_obj, attr, value)
            logging.error(
                'failed to save settings of info window to the '
                    'application settings object: %s',
                err)


class _InfoWin(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            obj: Any,
            title_cb: Callable[[Any], str],
            attrs_cb: Callable[[Any], Iterable[str]],
            close_cb: Callable[[Any], None],
            *,
            settings: _InfoWinSettings | None = None,
            ) -> None:
        super().__init__(master)
        self.resizable(True, True)
        #
        self._obj = obj
        """The object its attributes to be shown."""
        self._cbTitle = title_cb
        """The callback which gives a suitable title back for the object."""
        self._cbAttrs = attrs_cb
        """The callback which gives attributes of the object."""
        self._cbClose = close_cb
        """This callback saves settings just before close."""
        self.settings = settings if settings is not None else \
            _InfoWinSettings(0, 0, 400, 300, 150, 150,)
        #
        self._sheet = Sheet(self, headers=[_('KEY'), _('VALUE'),])
        self._sheet.column_width(0, self.settings.keyWidth)
        self._sheet.column_width(1, self.settings.valueWidth)
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
        self._setGeometry(not bool(settings))
        self.populateInfo()
        # Binding events...
        self.protocol('WM_DELETE_WINDOW', self.closeWin)
    
    def _setGeometry(self, center: bool) -> None:
        """Sets the geometry of this windows. `center` specifies whether
        to show this windows at the center of its parent window.
        """
        if center:
            self.geometry(f'{self.settings.width}x{self.settings.height}')
            self.after(10, self._centerDialog, self.master)
        else:
            self.geometry(
                f'{self.settings.width}x{self.settings.height}'
                f'+{self.settings.x}+{self.settings.y}')
    
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
            sett_obj: Any | None = None,
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
            sett_obj: Any | None = None,
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
        self._settObj = sett_obj if sett_obj is not None and \
            _InfoWinSettings.checkObj(sett_obj) else None
        self._infoWins = dict[int, _InfoWin]()
    
    def _getObjHash(self, obj: _T) -> int:
        """Gets the unique hash for provided object."""
        temp = obj
        if self._cbHash is not None:
            temp = self._cbHash(obj) # type: ignore
        return hash(temp)
    
    def showInfoWin(self, obj: _T) -> None:
        hash_ = self._getObjHash(obj)
        try:
            infoWin = self._infoWins[hash_]
        except KeyError:
            try:
                settings = _InfoWinSettings.fromObj(self._settObj) if \
                    self._settObj is not None else None
            except TypeError:
                settings = None
            infoWin = _InfoWin(
                self, # type: ignore
                obj,
                self._cbTitle,
                self._cbAttrs,
                self._onInfoWinClosed,
                settings=settings)
            self._infoWins[hash_] = infoWin
        else:
            infoWin.showWin()
    
    def _onInfoWinClosed(self, obj: _T) -> None:
        hash_ = self._getObjHash(obj)
        try:
            infoWin = self._infoWins[hash_]
        except KeyError:
            logging.debug(f'failed to find info window associated with {obj}')
        else:
            if self._settObj is not None:
                infoWin.settings.save(self._settObj)
            del self._infoWins[hash_]
    
    def closeInfoWin(self, obj: _T) -> None:
        hash_ = self._getObjHash(obj)
        try:
            infoWin = self._infoWins[hash_]
        except KeyError:
            logging.debug(f'failed to find info window associated with {obj}')
        else:
            infoWin.closeWin()
    
    def closeAllInfoWins(self) -> None:
        lsInfoWins = list(self._infoWins.values())
        for netWin in lsInfoWins[:-1]:
            netWin.destroy()
        try:
            lsInfoWins[-1].closeWin()
        except IndexError:
            pass
        self._infoWins.clear()
    
    def refreshInfoWin(self, obj: _T) -> None:
        hash_ = self._getObjHash(obj)
        try:
            infoWin = self._infoWins[hash_]
        except KeyError:
            pass
        else:
            infoWin.populateInfo()
