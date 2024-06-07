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
        self._svarName: tk.StringVar | None = None
        self._svarPrim: tk.StringVar | None = None
        self._svarSecod: tk.StringVar | None = None
        self._status = {
            'name': False,
            'primary': False,
            'secondary': True,}
        super().__init__(parent, 'Enter DNS server')
        if self._svarName is not None:
            self._svarName.set(name)
        if self._svarPrim is not None:
            self._svarPrim.set(primary)
        if self._svarSecod is not None:
            self._svarSecod.set(secondary)
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
        self._svarName = tk.StringVar(master)
        self._entry_name = ttk.Entry(
            master,
            textvariable=self._svarName,
            validate='key',
            validatecommand=(self.register(self._validateName), '%P'))
        self._entry_name.grid(column=1, row=0, padx=2, pady=2, sticky=tk.NSEW)
        #
        self._lbl_primary = ttk.Label(
            master,
            text='Primary:',
            foreground=self._invalidColor)
        self._lbl_primary.grid(column=0, row=1, padx=2, pady=2, sticky=tk.E)
        #
        self._svarPrim = tk.StringVar(master)
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
        self._svarSecod = tk.StringVar(master)
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
    
    def validate(self):
        return all(self._status[key] for key in self._status)
    
    def ok(self, event=None):
        if self.validate():
            self.result = DnsServer(
                self._svarName.get(),
                IPv4Address(self._svarPrim.get()),
                IPv4Address(self._svarSecod.get()) if self._svarSecod.get() \
                    else None)
            self.apply()
            self.withdraw()
            self.update_idletasks()
            self.cancel()

    def cancel(self, event=None):
        print("Custom Cancel behavior")
        super().cancel(event)
    
    def _validateInitials(self) -> None:
        self._validateName(self._svarName.get()) # type: ignore
        self._validatePrimary(self._svarPrim.get()) # type: ignore
        self._validateSecond(self._svarSecod.get()) # type: ignore
        #self._btn_ok.config(state=tk.NORMAL)
    
    def _validateName(self, text: str) -> bool:
        text = text.strip()
        if text and (not text in self._dnsNames):
            self._lbl_name.config(foreground=self._validColor)
            self._status['name'] = True
        else:
            self._lbl_name.config(foreground=self._invalidColor)
            self._status['name'] = False
        return True
    
    def _validatePrimary(self, text: str) -> bool:
        text = text.strip()
        try:
            IPv4Address(text)
            self._lbl_primary.config(foreground=self._validColor)
            self._status['primary'] = True
        except AddressValueError:
            self._lbl_primary.config(foreground=self._invalidColor)
            self._status['primary'] = False
        return True
    
    def _validateSecond(self, text: str) -> bool:
        text = text.strip()
        try:
            if text == '' or IPv4Address(text):
                self._lbl_secondary.config(foreground=self._validColor)
                self._status['secondary'] = True
        except AddressValueError:
            self._lbl_secondary.config(foreground=self._invalidColor)
            self._status['secondary'] = False
        return True
