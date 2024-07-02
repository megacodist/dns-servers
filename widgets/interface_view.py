#
# 
#

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable

from ntwrk import NetInt


class InterfaceView(tk.Frame):
    def __init__(
            self,
            master: tk.Misc,
            selection_cb: Callable[[int | None], None] | None = None,
            **kwargs,
            ) -> None:
        super().__init__(master, **kwargs)
        self._cbSelection = selection_cb
        self._canConn = 'green'
        self._noConn = '#ca482e'
        self._initGui()
        # Bindings...
        self._lstbx.bind("<<ListboxSelect>>", self._onSelection)
    
    def _initGui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        #
        self._vscrlbr = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL)
        self._hscrlbr = ttk.Scrollbar(
            self,
            orient=tk.HORIZONTAL)
        self._lstbx = tk.Listbox(
            self,
            xscrollcommand=self._hscrlbr.set,
            yscrollcommand=self._vscrlbr.set)  
        self._vscrlbr['command'] = self._lstbx.yview
        self._hscrlbr['command'] = self._lstbx.xview
        self._lstbx.grid(
            column=0,
            row=0,
            sticky=tk.NSEW)
        self._vscrlbr.grid(
            column=1,
            row=0,
            sticky=tk.NS)
        self._hscrlbr.grid(
            column=0,
            row=1,
            sticky=tk.EW)
    
    def _onSelection(self, _: tk.Event) -> None:
        selection = self._lstbx.curselection()
        if self._cbSelection:
            try:
                self._cbSelection(selection[0])
            except IndexError:
                self._cbSelection(None)
    
    def _getItemColor(self, net_int: NetInt) -> str:
        if net_int.connectivity():
            return self._canConn
        else:
            return self._noConn

    def populate(self, items: Iterable[NetInt]) -> None:
        self.clear()
        for item in items:
            self._lstbx.insert(tk.END, item['Name']) # type: ignore
            self._lstbx.itemconfig(tk.END, fg=self._getItemColor(item))
    
    def clear(self) -> None:
        self._lstbx.delete(0, tk.END)
    
    def getSelectedIdx(self) -> int | None:
        """Gets the index of selected interface."""
        try:
            return self._lstbx.curselection()[0]
        except IndexError:
            return None
