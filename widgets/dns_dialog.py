#
# 
#

from ipaddress import AddressValueError, IPv4Address
import tkinter as tk
from tkinter import ttk
import tkinter.simpledialog as TkSimpleDialog

from db import DnsServer


class DnsDialog(TkSimpleDialog.Dialog):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, 'Enter DNS server')
        self.resizable(width=False, height=False)
        self.result: DnsServer | None = None
        """The gathered DNS server information. If dialog is canceled, it
        will be `None`."""
        self._style = ttk.Style()
        self._style.configure("Valid.TEntry", fieldbackground="green")
        self._style.configure("Invalid.TEntry", fieldbackground="red")
    
    def body(self, master: tk.Frame) -> tk.Widget:
        master.columnconfigure(1, weight=1)
        master.config(padx=5, pady=5)
        #
        self._lbl_name = ttk.Label(master, text='Name:')
        self._lbl_name.grid(column=0, row=0, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_name = ttk.Entry(master)
        self._entry_name.grid(column=1, row=0, padx=2, pady=2, sticky=tk.NSEW)
        #
        self._lbl_primary = ttk.Label(master, text='Primary')
        self._lbl_primary.grid(column=0, row=1, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_primary = ttk.Entry(
            master,
            validate='key',
            validatecommand=(self.register(self._validatePrimary), '%P'))
        self._entry_primary.grid(
            column=1,
            row=1,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._lbl_secondary = ttk.Label(master, text='Secondary')
        self._lbl_secondary.grid(column=0, row=2, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_secondary = ttk.Entry(master)
        self._entry_secondary.grid(
            column=1,
            row=2,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        # 
        return self._entry_name
    
    def buttonbox(self):
        self._btnsBar = ttk.Frame(self)
        #
        self._btn_ok = ttk.Button(
            self._btnsBar,
            text="OK",
            width=10,
            command=self.ok,
            default=tk.ACTIVE)
        self._btn_ok.pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        #
        self._btn_cancel = ttk.Button(
            self._btnsBar,
            text="Cancel",
            width=10,
            command=self.cancel)
        self._btn_cancel.pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Escape>", self.cancel)
        #
        self._btnsBar.pack()
        
    def apply(self):
        name = self._entry_name.get().strip()
        primary = IPv4Address(self._entry_primary.get().strip())
        secondary = self._entry_primary.get().strip()
        secondary = None if secondary == '' else IPv4Address(secondary)
        self.result = DnsServer(
            name,
            primary,
            secondary)
    
    def _validatePrimary(self, a) -> bool:
        try:
            IPv4Address(a)
            self._entry_primary.config(style="Valid.TEntry")
        except AddressValueError:
            self._entry_primary.config(style="Invalid.TEntry")
        return True
