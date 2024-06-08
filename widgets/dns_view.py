#
# 
#

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, MutableSequence, TYPE_CHECKING

from db import DnsServer


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


class Dnsview(tk.Frame):
    def __init__(self, master: tk.Misc, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._initGui()
    
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
        self._trvw = ttk.Treeview(
            self,
            xscrollcommand=self._hscrlbr.set,
            yscrollcommand=self._vscrlbr.set)  
        self._vscrlbr['command'] = self._trvw.yview
        self._hscrlbr['command'] = self._trvw.xview
        self._trvw.grid(
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
        # Format columns
        self._trvw.config(columns=('#1', '#2', '#3',))
        self._trvw.column('#0', width=0, stretch=tk.NO)  # Hidden column for tree structure
        self._trvw.column(0, anchor=tk.W, width=100, stretch=False)
        self._trvw.column(1, anchor=tk.W, width=100, stretch=False)
        self._trvw.column(2, anchor=tk.W, width=100, stretch=False)
        # Create column headings
        self._trvw.heading('#0', text='', anchor=tk.W)  # Hidden heading for tree structure
        self._trvw.heading(0, text=_('NAME'), anchor=tk.W)
        self._trvw.heading(1, text=_('PRIMARY'), anchor=tk.W)
        self._trvw.heading(2, text=_('SECONDARY'), anchor=tk.W)
    
    def clear(self) -> None:
        """Clears all DNS servers from the View."""
        for child in self._trvw.get_children():
            self._trvw.delete(child)
    
    def getSetectedName(self) -> str | None:
        """Gets the name of the selected DNS server in the View. If
        nothing is selected, it returns `None`."""
        selection = self._trvw.selection()
        match len(selection):
            case 0:
                return None
            case 1:
                return self._trvw.item(selection[0], 'text')
            case _:
                logging.error(
                    'more than one item in the Dnsview is selected',
                    stack_info=True,)
    
    def populate(self, dnses: MutableSequence[DnsServer]) -> None:
        self.clear()
        for dns in dnses:
            self._trvw.insert(
                parent='',
                index=tk.END,
                values=(
                    dns.name,
                    str(dns.primary),
                    '' if dns.secondary is None else str(dns.secondary)))
    
    def appendDns(self, dns: DnsServer) -> None:
        self._trvw.insert(
            parent='',
            index=tk.END,
            values=(
                dns.name,
                str(dns.primary),
                '' if dns.secondary is None else str(dns.secondary)))
