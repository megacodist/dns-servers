#
# 
#

import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from tksheet import Sheet

from ntwrk import NetInt


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


class NetIntDialog(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            net_int: NetInt,
            ) -> None:
        super().__init__(master)
        self.title(_('NET_INT_INFO'))
        self.resizable(True, True)
        self.grab_set()
        #
        self._netInt = net_int
        #
        self._sheet = Sheet(self, show_row_index=False, show_header=False)
        self._sheet.pack(fill=tk.BOTH, expand=True)
        #
        self.after(10, self._centerDialog, master)
    
    def _centerDialog(self, parent: tk.Misc) -> None:
        _, x, y = parent.winfo_geometry().split('+')
        x = int(x) + (parent.winfo_width() - self.winfo_width()) // 2
        y = int(y) + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')
    
    def _populate(self) -> None:
        for attr in self._getAttrsName(self._netInt):
            self._sheet.insert_row([attr, getattr(self._netInt, attr)])
    
    def _getAttrsName(self, obj: object) -> tuple[str, ...]:
        attrs = [
            attr for attr in dir(obj)
            if not callable(getattr(self.__class__, attr)) and \
                attr[:2] != '__' and attr[-2:] != '__']
        attrs.sort(key=lambda x: x.lower())
        return tuple(attrs)
    
    def showDialog(self) -> None:
        """Shows the dialog box and returns a `DnsServer` on completion
        or `None` on cancelation.
        """
        self.wm_deiconify()
        self.wait_window()
