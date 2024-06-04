#
# 
#

import tkinter as tk
from tkinter import ttk
import tkinter.simpledialog as TkSimpleDialog


class DnsDialog(TkSimpleDialog.Dialog):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, 'Enter DNS server')
        self.dnsName: str
        self.primary: str
        self.secondary: str
    
    def body(self, master: tk.Frame) -> None:
        master.columnconfigure(1, weight=1)
        master.config(padx=3, pady=3)
        #
        self._lbl_name = tk.Label(master, text='Name')
        self._lbl_name.grid(column=0, row=0, sticky=tk.E)
        #
        self._entry_name = tk.Entry(master)
        self._entry_name.grid(column=1, row=0, sticky=tk.NSEW)
        #
        self._lbl_primary = tk.Label(master, text='Primary')
        self._lbl_primary.grid(column=0, row=1, sticky=tk.E)
        #
        self._entry_primary = tk.Entry(master)
        self._entry_primary.grid(column=1, row=1, sticky=tk.NSEW)
        #
        self._lbl_secondary = tk.Label(master, text='Secondary')
        self._lbl_secondary.grid(column=0, row=2, sticky=tk.E)
        #
        self._entry_secondary = tk.Entry(master)
        self._entry_secondary.grid(column=1, row=2, sticky=tk.NSEW)
        
    
    def apply(self):
        self.dnsName = self._entry_name.get()
        self.primary = self._entry_primary.get()
        self.secondary = self._entry_secondary.get()
