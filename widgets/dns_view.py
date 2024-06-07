#
# 
#

import tkinter as tk
from tkinter import ttk
from typing import MutableSequence

from db import DnsServer


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
        self._trvw.heading('#0', text="", anchor=tk.W)  # Hidden heading for tree structure
        self._trvw.heading(0, text="Name", anchor=tk.W)
        self._trvw.heading(1, text="Primary", anchor=tk.W)
        self._trvw.heading(2, text="Secondary", anchor=tk.W)
    
    def populate(self, dnses: MutableSequence[DnsServer]) -> None:
        for dns in dnses:
            self._trvw.insert(
                parent='',
                index=tk.END,
                values=(dns.name, dns.primary, dns.secondary))
    
    def addDns(self, dns: DnsServer) -> None:
        self._trvw.insert(
            parent='',
            index=tk.END,
            values=(dns.name, dns.primary, dns.secondary))
