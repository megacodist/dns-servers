#
# 
#

from ipaddress import AddressValueError, IPv4Address
import tkinter as tk
from tkinter import ttk
import tkinter.simpledialog as TkSimpleDialog

from db import DnsServer
from utils.sorted_list import SortedList


class DnsDialog(TkSimpleDialog.Dialog):
    def __init__(
            self,
            parent: tk.Misc,
            dns_names: SortedList[str],
            name: str = '',
            primary: str = '',
            secondary: str = '',
            ) -> None:
        self._validColor = 'green'
        self._invalidColor = '#ca482e'
        self.result: DnsServer | None = None
        """The gathered DNS server information. If dialog is canceled, it
        will be `None`."""
        self._dnsNames: SortedList[str] = dns_names
        self._svarName = tk.StringVar(self, name)
        self._svarPrim = tk.StringVar(self, primary)
        self._svarSecod = tk.StringVar(self, secondary)
        super().__init__(parent, 'Enter DNS server')
        self.after(10, self._validateInitials)
    
    def body(self, master: tk.Frame) -> tk.Widget:
        self.resizable(False, False)
        master.config(padx=5, pady=5)
        #
        self._lbl_name = ttk.Label(
            master,
            text='Name:',
            foreground=self._invalidColor)
        self._lbl_name.grid(column=0, row=0, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_name = ttk.Entry(master, textvariable=self._svarName)
        self._entry_name.grid(column=1, row=0, padx=2, pady=2, sticky=tk.NSEW)
        #
        self._lbl_primary = ttk.Label(
            master,
            text='Primary:',
            foreground=self._invalidColor)
        self._lbl_primary.grid(column=0, row=1, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_primary = ttk.Entry(
            master,
            textvariable=self._svarPrim,
            validate='key',
            validatecommand=(self.register(self._validatePrimary), '%P'))
        self._entry_primary.grid(
            column=1,
            row=1,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._lbl_secondary = ttk.Label(
            master,
            text='Secondary:',
            foreground=self._validColor)
        self._lbl_secondary.grid(column=0, row=2, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_secondary = ttk.Entry(
            master,
            textvariable=self._svarSecod,
            validate='key',
            validatecommand=(self.register(self._validateSecond), '%P'))
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
            state=tk.DISABLED,
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
    
    def _validateInitials(self) -> None:
        self._validatePrimary(self._svarPrim.get())
        self._validateSecond(self._svarSecod.get())
        self._btn_ok.config(state=tk.NORMAL)
    
    def _validateName(self, text: str) -> bool:
        text = text.strip()
        self._svarName.set(text)
        if text and (not text in self._dnsNames):
            self._lbl_name.config(foreground=self._validColor)
        else:
            self._lbl_primary.config(foreground=self._invalidColor)
        return True
    
    def _validatePrimary(self, text: str) -> bool:
        text = text.strip()
        self._svarPrim.set(text)
        try:
            IPv4Address(text)
            self._lbl_primary.config(foreground=self._validColor)
        except AddressValueError:
            self._lbl_primary.config(foreground=self._invalidColor)
        return True
    
    def _validateSecond(self, text: str) -> bool:
        text = text.strip()
        self._svarSecod.set(text)
        try:
            if text == '' or IPv4Address(text):
                self._lbl_secondary.config(foreground=self._validColor)
        except AddressValueError:
            self._lbl_secondary.config(foreground=self._invalidColor)
        return True
