#
# 
#

import enum
from ipaddress import (AddressValueError, IPv4Address as IPv4,
    IPv6Address as IPv6)
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from db import DnsServer


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


BAD_DNS_NAMES = ['arp', 'bgp', 'cifs', 'dhcp', 'firewall', 'ftp', 'gateway',
    'http', 'https', 'icmp', 'imap', 'ip', 'ldap', 'mac', 'nat', 'ntp',
    'ospf', 'pop3', 'rdp', 'router', 'smb', 'smtp', 'snmp', 'ssh', 'ssl',
    'subnet', 'switch', 'tcp', 'telnet', 'tls', 'udp', 'vlan', 'vnc', 'vpn']


class _DNS_ERRS(enum.IntFlag):
    OK = 0x000
    """Indicates that there is no error."""
    ALL_EMPTY = 0x001
    """Indicates that all IP fields are empty."""
    SAME_4 = 0x002
    """Indicates that both IPv4 addresses are the same."""
    SAME_6 = 0x004
    """Indicates that both IPv6 addresses are the same."""
    BAD_PRIM_4 = 0x008
    """Indicates that primary IPv4 address is not valid."""
    BAD_SECON_4 = 0x010
    """Indicates that secondary IPv4 address is not valid."""
    BAD_PRIM_6 = 0x020
    """Indicates that primary IPv6 address is not valid."""
    BAD_SECON_6 = 0x040
    """Indicates that secondary IPv6 address is not valid."""
    NO_NAME = 0x080
    """Indicates that no name is provided for the DNS server."""
    DUP_NAME = 0x100
    """Indicates that the name is already exists."""
    BAD_NAME = 0x200
    """Indicates that the name is not acceptable."""


_ERR_MSGS: dict[_DNS_ERRS, str] = {
    _DNS_ERRS.ALL_EMPTY: _('ALL_IPS_EMPTY'),
    _DNS_ERRS.SAME_4: _('SAME_IPV4'),
    _DNS_ERRS.SAME_6: _('SAME_IPV6'),
    _DNS_ERRS.BAD_PRIM_4: _('BAD_PRIM_IP4'),
    _DNS_ERRS.BAD_SECON_4: _('BAD_SECON_IP4'),
    _DNS_ERRS.BAD_PRIM_6: _('BAD_PRIM_IP6'),
    _DNS_ERRS.BAD_SECON_6: _('BAD_SECON_IP6'),
    _DNS_ERRS.NO_NAME: _('EMPTY_DNS_NAME'),
    _DNS_ERRS.DUP_NAME: _('DUPLICATE_DNS_NAME'),
    _DNS_ERRS.BAD_NAME: _('BAD_DNS_NAME'),}


class _IP_IDX(enum.IntEnum):
    PRIM_4 = 0
    SECON_4 = 1
    PRIM_6 = 2
    SECON_6 = 3


_mpIdxErr: dict[_IP_IDX, _DNS_ERRS] = {
    _IP_IDX.PRIM_4: _DNS_ERRS.BAD_PRIM_4,
    _IP_IDX.SECON_4: _DNS_ERRS.BAD_SECON_4,
    _IP_IDX.PRIM_6: _DNS_ERRS.BAD_PRIM_6,
    _IP_IDX.SECON_6: _DNS_ERRS.BAD_SECON_6,}
"""The mapping between IP index enumeartions and DNS errors."""


_mpIdxSame: dict[_IP_IDX, _DNS_ERRS] = {
    _IP_IDX.PRIM_4: _DNS_ERRS.SAME_4,
    _IP_IDX.SECON_4: _DNS_ERRS.SAME_4,
    _IP_IDX.PRIM_6: _DNS_ERRS.SAME_6,
    _IP_IDX.SECON_6: _DNS_ERRS.SAME_6,}
"""The mapping between IP index and IPv4 or IPv6 equality."""


class _LblIpSvar:
    def __init__(
            self,
            lbl: ttk.Label,
            entry: ttk.Entry,
            ip: IPv4 | IPv6 | None,
            svar: tk.StringVar,
            ) -> None:
        self.lbl = lbl
        self.entry = entry
        self.ip = ip
        self.svar = svar


class DnsDialog(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            mp_name_dns: dict[str, DnsServer],
            dns: DnsServer | None = None,
            ) -> None:
        super().__init__(master)
        self.title(_('ENTER_DNS'))
        self.resizable(False, False)
        self.grab_set()
        # Defining variables...
        from utils.funcs import ipToStr
        # Defning variables...
        self._mpNameDns: dict[str, DnsServer]
        """The mappin from DNS names to DNS objects: `name -> dns`"""
        self._okColor = 'green'
        """The color name that indicates the item is acceptable."""
        self._errColor = '#ca482e'
        """The color name that indicates something is wrong with the item."""
        self._result: DnsServer | None = None
        """The gathered DNS server information. If dialog is canceled, it
        will be `None`."""
        self._errs = _DNS_ERRS.OK
        self._mpNameDns = mp_name_dns
        # Initializing StringVars...
        if dns is None:
            self._svarName = tk.StringVar(self, '')
            self._svarPrim4 = tk.StringVar(self, '')
            self._svarSecod4 = tk.StringVar(self, '')
            self._svarPrim6 = tk.StringVar(self, '')
            self._svarSecon6 = tk.StringVar(self, '')
        elif isinstance(dns, DnsServer):
            self._svarName = tk.StringVar(self, dns.name)
            self._svarPrim4 = tk.StringVar(self, ipToStr(dns.prim_4))
            self._svarSecod4 = tk.StringVar(self, ipToStr(dns.secon_4))
            self._svarPrim6 = tk.StringVar(self, ipToStr(dns.prim_6))
            self._svarSecon6 = tk.StringVar(self, ipToStr(dns.secon_6))
            self._mpNameDns = mp_name_dns.copy()
        else:
            raise TypeError("'dns' argument of the initializer of "
                f"{self.__class__.__qualname__} must be either None "
                f"or {DnsServer.__qualname__}")
        # Initializing the GUI...
        self._initGui()
        #
        self._ipsData: dict[_IP_IDX, _LblIpSvar] = {
            _IP_IDX.PRIM_4: _LblIpSvar(
                self._lbl_prim_4,
                self._entry_prim_4,
                None if dns is None else dns.prim_4,
                self._svarPrim4,),
            _IP_IDX.SECON_4: _LblIpSvar(
                self._lbl_secon_4,
                self._entry_secon_4,
                None if dns is None else dns.secon_4,
                self._svarSecod4,),
            _IP_IDX.PRIM_6: _LblIpSvar(
                self._lbl_prim_6,
                self._entry_prim_6,
                None if dns is None else dns.prim_6,
                self._svarPrim6),
            _IP_IDX.SECON_6: _LblIpSvar(
                self._lbl_secon_6,
                self._entry_secon_6,
                None if dns is None else dns.secon_6,
                self._svarSecon6),}
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
        ips = filter(
            None,
            [self._ipsData[idx].ip for idx in self._ipsData.keys()])
        self._result = DnsServer(
            self._svarName.get(),
            *list(ips))
        self.destroy()

    def _onCanceled(self) -> None:
        self._result = None
        self.destroy()
    
    def _initGui(self) -> None:
        from functools import partial
        #
        self._frm_container = ttk.Frame(self)
        self._frm_container.pack(fill=tk.BOTH, expand=True)
        #
        self._lbl_name = ttk.Label(
            self._frm_container,
            text=_('NAME') + ':',)
        self._lbl_name.grid(row=0, column=0, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_name = ttk.Entry(
            self._frm_container,
            textvariable=self._svarName,
            validate='key',
            validatecommand=(self.register(self._validateName), '%P'))
        self._entry_name.grid(row=0, column=1, padx=2, pady=2, sticky=tk.NSEW)
        #
        self._lbl_prim_4 = ttk.Label(
            self._frm_container,
            text=_('PRIM_4') + ':',)
        self._lbl_prim_4.grid(row=1, column=0, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_prim_4 = ttk.Entry(
            self._frm_container,
            textvariable=self._svarPrim4,
            validate='key',
            validatecommand=(self.register(
                partial(self._validateIp, idx=_IP_IDX.PRIM_4)),
                '%P'))
        self._entry_prim_4.grid(
            row=1,
            column=1,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._lbl_secon_4 = ttk.Label(
            self._frm_container,
            text=_('SECON_4') + ':',)
        self._lbl_secon_4.grid(row=2, column=0, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_secon_4 = ttk.Entry(
            self._frm_container,
            textvariable=self._svarSecod4,
            validate='key',
            validatecommand=(self.register(
                partial(self._validateIp, idx=_IP_IDX.SECON_4)),
                '%P'))
        self._entry_secon_4.grid(
            row=2,
            column=1,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._lbl_prim_6 = ttk.Label(
            self._frm_container,
            text=_('PRIM_6') + ':',)
        self._lbl_prim_6.grid(row=3, column=0, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_prim_6 = ttk.Entry(
            self._frm_container,
            textvariable=self._svarPrim6,
            validate='key',
            validatecommand=(self.register(
                partial(self._validateIp, idx=_IP_IDX.PRIM_6)),
                '%P'))
        self._entry_prim_6.grid(
            row=3,
            column=1,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._lbl_secon_6 = ttk.Label(
            self._frm_container,
            text=_('SECON_6') + ':',)
        self._lbl_secon_6.grid(row=4, column=0, padx=2, pady=2, sticky=tk.E)
        #
        self._entry_secon_6 = ttk.Entry(
            self._frm_container,
            textvariable=self._svarSecon6,
            validate='key',
            validatecommand=(self.register(
                partial(self._validateIp, idx=_IP_IDX.SECON_6)),
                '%P'))
        self._entry_secon_6.grid(
            row=4,
            column=1,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._lfrm_errors = ttk.LabelFrame(
            self._frm_container,
            text=_('ERRORS'))
        self._lfrm_errors.rowconfigure(0, weight=1)
        self._lfrm_errors.grid(
            row=5,
            column=0,
            columnspan=2,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._hscrlbr = ttk.Scrollbar(
            self._lfrm_errors,
            orient=tk.HORIZONTAL)
        self._txt = tk.Text(
            self._lfrm_errors,
            height=6,
            width=24,
            wrap=tk.NONE,
            state=tk.DISABLED,
            xscrollcommand=self._hscrlbr.set,)  
        self._hscrlbr.config(command=self._txt.xview)
        self._txt.grid(
            column=0,
            row=0,
            sticky=tk.NSEW)
        self._hscrlbr.grid(
            column=0,
            row=1,
            sticky=tk.EW)
        #
        self._frm_btns = ttk.Frame(self._frm_container)
        self._frm_btns.grid(
            row=6,
            column=0,
            columnspan=2,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._btn_ok = ttk.Button(
            self._frm_btns,
            text=_('OK'),
            width=10,
            command=self._onApproved,
            default=tk.ACTIVE)
        self._btn_ok.pack(side=tk.RIGHT, padx=5, pady=5)
        #
        self._btn_cancel = ttk.Button(
            self._frm_btns,
            text=_('CANCEL'),
            width=10,
            command=self._onCanceled)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def _validateInitials(self) -> None:
        self._validateName(self._svarName.get())
        for ipIdx in self._ipsData.keys():
            self._validateIp(self._ipsData[ipIdx].svar.get(), ipIdx)
    
    def _validateName(self, text: str) -> bool:
        text = text.strip()
        self._svarName.set(text)
        self._entry_name.icursor(tk.END)
        if not text:
            # Reporting empty name error...
            self._errs |= _DNS_ERRS.NO_NAME
            self._errs &= (~_DNS_ERRS.BAD_NAME)
            self._errs &= (~_DNS_ERRS.DUP_NAME)
            self._lbl_name.config(foreground=self._errColor)
        else:
            self._errs &= (~_DNS_ERRS.NO_NAME)
            if text.lower() in BAD_DNS_NAMES:
                # Reporting bad DNS name error...
                self._errs |= _DNS_ERRS.BAD_NAME
                self._errs &= (~_DNS_ERRS.DUP_NAME)
                self._lbl_name.config(foreground=self._errColor)
            else:
                self._errs &= (~_DNS_ERRS.BAD_NAME)
                if text in self._mpNameDns:
                    # Reporting duplicate name error...
                    self._errs |= _DNS_ERRS.DUP_NAME
                    self._lbl_name.config(foreground=self._errColor)
                else:
                    self._errs &= (~_DNS_ERRS.DUP_NAME)
                    # Reporting name's OK...
                    self._lbl_name.config(foreground=self._okColor)
        self._updateErrMsgOkBtn()
        return True
    
    def _validateIp(self, text: str, idx: _IP_IDX) -> bool:
        text = text.strip()
        self._ipsData[idx].svar.set(text)
        self._ipsData[idx].entry.icursor(tk.END)
        # Checking against empty IPs...
        if not text:
            self._errs &= ~_mpIdxErr[idx]
            self._errs &= ~_mpIdxSame[idx]
            if self._allIpsEmpty():
                self._errs |= _DNS_ERRS.ALL_EMPTY
                self._changeAllColors(self._errColor)
            else:
                self._errs &= ~_DNS_ERRS.ALL_EMPTY
                self._changeColor(idx, self._okColor)
            self._updateErrMsgOkBtn()
            return True
        # Checking against comming out of `ALL_EMPTY` state...
        if self._errs & _DNS_ERRS.ALL_EMPTY:
            self._errs &= ~_DNS_ERRS.ALL_EMPTY
            self._changeAllColors(self._okColor)
        # Checking against validity of IPv4...
        if idx == _IP_IDX.PRIM_4 or idx == _IP_IDX.SECON_4:
            try:
                self._ipsData[idx].ip = IPv4(text)
                self._errs &= ~_mpIdxErr[idx]
            except AddressValueError:
                self._ipsData[idx].ip = None
                self._errs |= _mpIdxErr[idx]
                if self._errs & _mpIdxSame[idx]:
                    self._errs &= ~_mpIdxSame[idx]
                    self._changeBothColor(idx, self._okColor)
                self._changeColor(idx, self._errColor)
                self._updateErrMsgOkBtn()
                return True
            # Checking that IPv4 addresses are the same...
            if self._ipsData[_IP_IDX.PRIM_4].ip and self._ipsData[
                    _IP_IDX.SECON_4].ip and self._ipsData[_IP_IDX.PRIM_4].ip \
                    == self._ipsData[_IP_IDX.SECON_4].ip:
                self._errs |= _DNS_ERRS.SAME_4
                self._changeBothColor(idx, self._errColor)
            else:
                if self._errs & _DNS_ERRS.SAME_4:
                    self._errs &= ~_DNS_ERRS.SAME_4
                    self._changeBothColor(idx, self._okColor)
                self._changeColor(idx, self._okColor)
            self._updateErrMsgOkBtn()
            return True
        # Checking against validity of IPv6...
        try:
            self._ipsData[idx].ip = IPv6(text)
            self._errs &= ~_mpIdxErr[idx]
        except AddressValueError:
            self._ipsData[idx].ip = None
            self._errs |= _mpIdxErr[idx]
            if self._errs & _mpIdxSame[idx]:
                self._errs &= ~_mpIdxSame[idx]
                self._changeBothColor(idx, self._okColor)
            self._changeColor(idx, self._errColor)
            self._updateErrMsgOkBtn()
            return True
        # Checking that IPv4 addresses are the same...
        if self._ipsData[_IP_IDX.PRIM_6].ip and self._ipsData[
                _IP_IDX.SECON_6].ip and self._ipsData[_IP_IDX.PRIM_6].ip \
                == self._ipsData[_IP_IDX.SECON_6].ip:
            self._errs |= _DNS_ERRS.SAME_6
            self._changeBothColor(idx, self._errColor)
        else:
            if self._errs & _DNS_ERRS.SAME_6:
                self._errs &= ~_DNS_ERRS.SAME_6
                self._changeBothColor(idx, self._okColor)
            self._changeColor(idx, self._okColor)
        self._updateErrMsgOkBtn()
        return True
    
    def _allIpsEmpty(self) -> bool:
        return not any(
            self._ipsData[idx].svar.get()
            for idx in self._ipsData.keys())
    
    def _changeAllColors(self, color: str) -> None:
        for ipIdx in self._ipsData.keys():
            self._ipsData[ipIdx].lbl.config(foreground=color)
    
    def _changeBothColor(self, idx: _IP_IDX, color: str) -> None:
        if idx == _IP_IDX.PRIM_4 or idx == _IP_IDX.SECON_4:
            self._ipsData[_IP_IDX.PRIM_4].lbl.config(foreground=color)
            self._ipsData[_IP_IDX.SECON_4].lbl.config(foreground=color)
        elif idx == _IP_IDX.PRIM_6 or idx == _IP_IDX.SECON_6:
            self._ipsData[_IP_IDX.PRIM_6].lbl.config(foreground=color)
            self._ipsData[_IP_IDX.SECON_6].lbl.config(foreground=color)
    
    def _changeColor(self, ip_idx: _IP_IDX, color: str) -> None:
        self._ipsData[ip_idx].lbl.config(foreground=color)
    
    def _updateErrMsgOkBtn(self) -> None:
        """Updates error messages and OK button enability."""
        msg = '\n'.join(_ERR_MSGS[errCode] for errCode in self._errs)
        self._txt.config(state=tk.NORMAL)
        self._txt.delete("1.0", tk.END)
        self._txt.insert(tk.END, msg)
        self._txt.config(state=tk.DISABLED)
        if self._errs:
            self._btn_ok.config(state=tk.DISABLED)
        else:
            self._btn_ok.config(state=tk.NORMAL)
    
    def showDialog(self) -> DnsServer | None:
        """Shows the dialog box and returns a `DnsServer` on completion
        or `None` on cancelation.
        """
        self.wm_deiconify()
        self.wait_window()
        return self._result
