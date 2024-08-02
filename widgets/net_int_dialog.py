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


class WmiNetDialog(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            net_bag: AdapCfgBag,
            idx: ACIdx,
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
        self.grab_set()
        #
        self._bag = net_bag
        self.title(self._getTitle(idx))
        self._idx: ACIdx
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
        self.changeIdx(idx, net_bag)
        if xy is None:
            self.after(10, self._centerDialog, master)
        else:
            self.geometry(f'+{xy[0]}+{xy[1]}')
        # Binding events...
        self.protocol('WM_DELETE_WINDOW', self._onClosing)
    
    def changeIdx(
            self,
            idx: ACIdx,
            bag: AdapCfgBag | None = None,
            ) -> None:
        self._idx = idx
        if bag is not None:
            self._bag = bag
        self._populate()
    
    def _getTitle(self, idx: ACIdx) -> str:
        item = self._bag[idx]
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
                'Cannot get the geometry of the WmiNetDialog.',
                stack_info=True)
        self.destroy()
    
    def _populate(self) -> None:
        from ntwrk import AbsNet
        baseNet: AbsNet = self._bag[self._idx]
        for attr in baseNet.getAttrs():
            self._sheet.insert_row([attr, getattr(baseNet, attr)])
    
    def showDialog(self) -> None:
        """Shows the dialog box and returns a `DnsServer` on completion
        or `None` on cancelation.
        """
        self.wm_deiconify()
        self.wait_window()
