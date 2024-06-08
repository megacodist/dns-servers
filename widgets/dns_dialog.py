#
# 
#

from ipaddress import AddressValueError, IPv4Address
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from db import DnsServer
from utils.sorted_list import SortedList

if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


class _DataStatus:
    def __init__(self, data: str | IPv4Address | None, status: bool) -> None:
        self.data = data
        self.status = status


class DnsDialog(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            dns_names: SortedList[str],
            name: str = '',
            primary: str = '',
            secondary: str = '',
            ) -> None:
        super().__init__(master)
        self.title(_('ENTER_DNS'))
        self.resizable(False, False)
        self.grab_set()
        # Defning variables...
        self._validColor = 'green'
        self._invalidColor = '#ca482e'
        self._result: DnsServer | None = None
        """The gathered DNS server information. If dialog is canceled, it
        will be `None`."""
        self._dnsNames: SortedList[str] = dns_names
        self._svarName = tk.StringVar(self, name)
        self._svarPrim = tk.StringVar(self, primary)
        self._svarSecod = tk.StringVar(self, secondary)
        self._fields = {
            'name': _DataStatus(None, False),
            'primary': _DataStatus(None, False),
            'secondary': _DataStatus(None, False),}
        # Initializing the GUI...
        self._initGui()
        self._validateInitials()
        # Bindings...
        self.bind('<Return>', lambda _: self._onApproved())
        self.bind('<Escape>', lambda _: self._onCanceled())
        self.protocol('WM_DELETE_WINDOW', self._onCanceled)
        #
        self.after(10, self._centerDialog, master)
    
    def _centerDialog(self, parent: tk.Misc) -> None:
        _, x, y = parent.winfo_geometry().split('+')
        x = int(x) + (parent.winfo_width() - self.winfo_width()) // 2
        y = int(y) + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')
    
    def _onApproved(self) -> None:
        self._result = DnsServer(
            self._fields['name'].data, # type: ignore
            self._fields['primary'].data,  # type: ignore
            self._fields['secondary'].data)  # type: ignore
        self.destroy()

    def _onCanceled(self) -> None:
        self._result = None
        self.destroy()
    
    def _initGui(self) -> None:
        #
        self._frm_container = ttk.Frame(self)
        self._frm_container.pack(fill=tk.BOTH, expand=True)
        #
        self._lbl_name = ttk.Label(
            self._frm_container,
            text=_('NAME') + ':',
            foreground=self._invalidColor)
        self._lbl_name.grid(row=0, column=0, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_name = ttk.Entry(
            self._frm_container,
            textvariable=self._svarName,
            validate='key',
            validatecommand=(self.register(self._validateName), '%P'))
        self._entry_name.grid(row=0, column=1, padx=2, pady=2, sticky=tk.NSEW)
        #
        self._lbl_primary = ttk.Label(
            self._frm_container,
            text=_('primary') + ':',
            foreground=self._invalidColor)
        self._lbl_primary.grid(row=1, column=0, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_primary = ttk.Entry(
            self._frm_container,
            textvariable=self._svarPrim,
            validate='key',
            validatecommand=(self.register(self._validatePrimary), '%P'))
        self._entry_primary.grid(
            row=1,
            column=1,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._lbl_secondary = ttk.Label(
            self._frm_container,
            text=_('SECONDARY') + ':',
            foreground=self._validColor)
        self._lbl_secondary.grid(row=2, column=0, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_secondary = ttk.Entry(
            self._frm_container,
            textvariable=self._svarSecod,
            validate='key',
            validatecommand=(self.register(self._validateSecond), '%P'))
        self._entry_secondary.grid(
            row=2,
            column=1,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._frm_btns = ttk.Frame(self._frm_container)
        self._frm_btns.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._btn_ok = ttk.Button(
            self._frm_btns,
            text="OK",
            width=10,
            command=self._onApproved,
            default=tk.ACTIVE)
        self._btn_ok.pack(side=tk.RIGHT, padx=5, pady=5)
        #
        self._btn_cancel = ttk.Button(
            self._frm_btns,
            text="Cancel",
            width=10,
            command=self._onCanceled)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def _isInputValid(self) -> bool:
        return all(self._fields[key].status for key in self._fields)
    
    def _validateInitials(self) -> None:
        self._validateName(self._svarName.get())
        self._validatePrimary(self._svarPrim.get())
        self._validateSecond(self._svarSecod.get())
    
    def _validateName(self, text: str) -> bool:
        text = text.strip()
        if text and (not text in self._dnsNames):
            self._fields['name'].data = text
            self._fields['name'].status = True
            self._lbl_name.config(foreground=self._validColor)
            if self._isInputValid():
                self._btn_ok.config(state=tk.NORMAL)
        else:
            self._lbl_name.config(foreground=self._invalidColor)
            self._fields['name'].status = False
            self._btn_ok.config(state=tk.DISABLED)
        return True
    
    def _validatePrimary(self, text: str) -> bool:
        text = text.strip()
        try:
            ip = IPv4Address(text)
            self._fields['primary'].data = ip
            self._fields['primary'].status = True
            self._lbl_primary.config(foreground=self._validColor)
            if self._isInputValid():
                self._btn_ok.config(state=tk.NORMAL)
        except AddressValueError:
            self._fields['primary'].status = False
            self._lbl_primary.config(foreground=self._invalidColor)
            self._btn_ok.config(state=tk.DISABLED)
        return True
    
    def _validateSecond(self, text: str) -> bool:
        text = text.strip()
        try:
            if text == '' or (ip := IPv4Address(text)):
                self._fields['secondary'].data = ip if text else None # type: ignore
                self._fields['secondary'].status = True
                self._lbl_secondary.config(foreground=self._validColor)
                if self._isInputValid():
                    self._btn_ok.config(state=tk.NORMAL)
        except AddressValueError:
            self._lbl_secondary.config(foreground=self._invalidColor)
            self._fields['secondary'].status = False
            self._btn_ok.config(state=tk.DISABLED)
        return True
    
    def showDialog(self) -> DnsServer | None:
        """Shows the dialog box and returns a `DnsServer` on completion
        or `None` on cancelation.
        """
        self.wm_deiconify()
        self.wait_window()
        return self._result
