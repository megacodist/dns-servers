#
# 
#

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING, NamedTuple, Sequence

from tksheet import Sheet

from ntwrk import ACIdx, AdapCfgBag, NetAdap, NetConfig


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


class NetIntDlgSettings(NamedTuple):
    x: int
    y: int
    width: int
    height: int
    key_width: int
    value_int: int


class NetItemInfoWin(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            ac_bag: AdapCfgBag,
            idx: ACIdx,
            close_cb: Callable[[ACIdx], None] | None = None,
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
        self._cbClose = close_cb
        self._bag = ac_bag
        self._idx = idx
        self.title(self._getTitle())
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
        self.settings = NetIntDlgSettings(
            0,
            0,
            width,
            height,
            key_width,
            value_width)
        self.populate()
        if xy is None:
            self.after(10, self._centerDialog, master)
        else:
            self.geometry(f'+{xy[0]}+{xy[1]}')
        # Binding events...
        self.protocol('WM_DELETE_WINDOW', self._onClosing)
    
    def _getTitle(self) -> str:
        item = self._bag[self._idx]
        if isinstance(item, NetAdap):
            return item.NetConnectionID
        elif isinstance(item, NetConfig):
            return str(item.Index)
        else:
            logging.error('expected NetAdap or NetConfig, got '
                f'{item.__class__.__qualname__}')
            return item.__class__.__qualname__
    
    def _centerDialog(self, parent: tk.Misc) -> None:
        _, x, y = parent.winfo_geometry().split('+')
        x = int(x) + (parent.winfo_width() - self.winfo_width()) // 2
        y = int(y) + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')
    
    def _onClosing(self) -> None:
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
            self.settings = NetIntDlgSettings(
                int(match.group('x')),
                int(match.group('y')),
                int(match.group('width')),
                int(match.group('height')),
                int(colsWidths[0]),
                int(colsWidths[1]),)
        else:
            logging.error(
                'Cannot get the geometry of the NetItemInfoWin.',
                stack_info=True)
        if self._cbClose:
            self.after(100, self._cbClose, self._idx)
            #self._cbClose(self._idx)
        self.destroy()
    
    def _clear(self) -> None:
        count = len(self._sheet.get_sheet_data())
        for idx in reversed(range(count)):
            self._sheet.delete_row(idx)
    
    def populate(self) -> None:
        from ntwrk import AbsNet
        self._clear()
        netItem: AbsNet = self._bag[self._idx]
        for attr in netItem.getAttrs():
            self._sheet.insert_row([attr, getattr(netItem, attr)])
    
    def showWin(self) -> None:
        """Shows the window."""
        self.grab_set()
        self.mainloop()
    
    def showDialog(self) -> None:
        """Shows the window as dialog box."""
        self.grab_set()
        self.wm_deiconify()
        self.wait_window()
