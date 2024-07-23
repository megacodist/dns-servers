#
# 
#

import enum
from ipaddress import (AddressValueError, IPv4Address as IPv4,
    IPv6Address as IPv6)
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from db import DnsServer, IPRole


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


BAD_DNS_NAMES = ['arp', 'bgp', 'cifs', 'dhcp', 'firewall', 'ftp', 'gateway',
    'http', 'https', 'icmp', 'imap', 'ip', 'ldap', 'mac', 'nat', 'ntp',
    'ospf', 'pop3', 'rdp', 'router', 'smb', 'smtp', 'snmp', 'ssh', 'ssl',
    'subnet', 'switch', 'tcp', 'telnet', 'tls', 'udp', 'vlan', 'vnc', 'vpn']


class _DnsNameErrs(enum.IntEnum):
    OK = 0
    NO_NAME = 1
    """Indicates that no name is provided for the DNS server."""
    DUP_NAME = 2
    """Indicates that the name is already exists."""
    BAD_NAME = 3
    """Indicates that the name is not acceptable."""


class _IpVer(enum.IntEnum):
    V4 = 0
    V6 = 1


_mpRoleMoid: dict[IPRole, str] = {
    IPRole.PRIM_4: 'PRIM_4',
    IPRole.SECON_4: 'SECON_4',
    IPRole.PRIM_6: 'PRIM_6',
    IPRole.SECON_6: 'SECON_6',}
"""The mapping between `IPRole` objects and corresponding ID in MO files."""


_mpVerMoid: dict[_IpVer, str] = {
    _IpVer.V4: 'IPV4',
    _IpVer.V6: 'IPV6',}


_mpRoleVer: dict[IPRole, _IpVer] = {
    IPRole.PRIM_4: _IpVer.V4,
    IPRole.SECON_4: _IpVer.V4,
    IPRole.PRIM_6: _IpVer.V6,
    IPRole.SECON_6: _IpVer.V6,}
"""The mapping between IP role and the version of IP protocol."""


class _DnsErrs:
    def __init__(self) -> None:
        self.noIp = False
        self.sameVers = set[_IpVer]()
        self.badIps = set[IPRole]()
        self.dupIps = set[IPRole]()
        self.nameErr = _DnsNameErrs.OK


_NAME_MSGS: dict[_DnsNameErrs, str] = {
    _DnsNameErrs.NO_NAME: _('EMPTY_DNS_NAME'),
    _DnsNameErrs.DUP_NAME: _('DUPLICATE_DNS_NAME'),
    _DnsNameErrs.BAD_NAME: _('BAD_DNS_NAME'),}


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
            mp_ip_dns: dict[IPv4 | IPv6, DnsServer],
            dns: DnsServer | None = None,
            ) -> None:
        """A dialog to ask user for a new DNS server or change one. Arguments
        are as follow:
        * `mp_name_dns`: the mapping between available DNS names and their
        objects. The user provided name must not exist in the keys of this
        argument.
        * `mp_ip_dns`: the mapping between available DNS IPs and their
        objects. The user provided IPs must not exist in the keys of this
        argument.
        * `dns`: the DNS server object to change. If it is `None`, asks
        the user for a new DNS.
        """
        super().__init__(master)
        self.title(_('ENTER_DNS'))
        self.resizable(False, False)
        self.grab_set()
        # Defining variables...
        from utils.funcs import ipToStr
        # Defning variables...
        self._okColor = 'green'
        """The color name that indicates the item is acceptable."""
        self._errColor = '#ca482e'
        """The color name that indicates something is wrong with the item."""
        self._result: DnsServer | None = None
        """The gathered DNS server information. If dialog is canceled, it
        will be `None`."""
        self._errs = _DnsErrs()
        self._mpNameDns = mp_name_dns
        """The mappin from DNS names to DNS objects: `name -> dns`"""
        self._mpIpDns = mp_ip_dns
        """The mappin from each DNS ip to DNS objects: `IP -> dns`"""
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
        else:
            raise TypeError("'dns' argument of the initializer of "
                f"{self.__class__.__qualname__} must be either None "
                f"or {DnsServer.__qualname__}")
        # Initializing the GUI...
        self._initGui()
        #
        self._ipsData: dict[IPRole, _LblIpSvar] = {
            IPRole.PRIM_4: _LblIpSvar(
                self._lbl_prim_4,
                self._entry_prim_4,
                None if dns is None else dns.prim_4,
                self._svarPrim4,),
            IPRole.SECON_4: _LblIpSvar(
                self._lbl_secon_4,
                self._entry_secon_4,
                None if dns is None else dns.secon_4,
                self._svarSecod4,),
            IPRole.PRIM_6: _LblIpSvar(
                self._lbl_prim_6,
                self._entry_prim_6,
                None if dns is None else dns.prim_6,
                self._svarPrim6),
            IPRole.SECON_6: _LblIpSvar(
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
            self._svarName.get().strip(),
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
                partial(self._validateIp, role=IPRole.PRIM_4)),
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
                partial(self._validateIp, role=IPRole.SECON_4)),
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
                partial(self._validateIp, role=IPRole.PRIM_6)),
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
                partial(self._validateIp, role=IPRole.SECON_6)),
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
        for role in self._ipsData.keys():
            self._validateIp(self._ipsData[role].svar.get(), role)
    
    def _validateName(self, text: str) -> bool:
        text = text.strip()
        if not text:
            # Reporting empty name error...
            self._errs.nameErr = _DnsNameErrs.NO_NAME
            self._lbl_name.config(foreground=self._errColor)
        elif text.lower() in BAD_DNS_NAMES:
            # Reporting bad DNS name error...
            self._errs.nameErr = _DnsNameErrs.BAD_NAME
            self._lbl_name.config(foreground=self._errColor)
        elif text in self._mpNameDns:
            # Reporting duplicate name error...
            self._errs.nameErr = _DnsNameErrs.DUP_NAME
            self._lbl_name.config(foreground=self._errColor)
        else:
            self._errs.nameErr = _DnsNameErrs.OK
            # Reporting name's OK...
            self._lbl_name.config(foreground=self._okColor)
        self._updateErrMsgOkBtn()
        return True
    
    def _validateIp(self, text: str, role: IPRole) -> bool:
        text = text.strip()
        # Checking against empty IPs...
        if not text:
            if self._allIpsEmpty():
                self._errs.noIp = True
                self._changeAllColors(self._errColor)
                # Clearing other IP-related errors...
                self._errs.sameVers.clear()
                self._errs.badIps.clear()
                self._errs.dupIps.clear()
            else:
                self._changeColor(role, self._okColor)
                # Clearing other IP-related errors for this IP...
                try:
                    self._errs.sameVers.remove(_mpRoleVer[role])
                except KeyError:
                    pass
                try:
                    self._errs.badIps.remove(role)
                except KeyError:
                    pass
                try:
                    self._errs.dupIps.remove(role)
                except KeyError:
                    pass
            self._updateErrMsgOkBtn()
            return True
        # Checking against comming out of `ALL_EMPTY` state...
        if self._errs.noIp:
            self._errs.noIp = False
            self._changeAllColors(self._okColor)
        #
        try:
            self._ipsData[role].ip = IPv4(text)
            try:
                self._errs.badIps.remove(role)
            except KeyError:
                pass
        except AddressValueError:
            try:
                self._ipsData[role].ip = IPv6(text)
                try:
                    self._errs.badIps.remove(role)
                except KeyError:
                    pass
            except AddressValueError:
                self._ipsData[role].ip = None
                self._errs.badIps.add(role)
                if _mpRoleVer[role] in self._errs.sameVers:
                    self._errs.sameVers.remove(_mpRoleVer[role])
                    self._chnagePeerColor(role, self._okColor)
                if role in self._errs.dupIps:
                    self._errs.dupIps.remove(role)
                self._changeColor(role, self._errColor)
                self._updateErrMsgOkBtn()
                return True
        self._changeColor(role, self._okColor)
        # Checking against duplicate IPs...
        if self._ipsData[role].ip in self._mpIpDns:
            self._errs.dupIps.add(role)
            self._changeColor(role, self._errColor)
        elif role in self._errs.dupIps:
            self._errs.dupIps.remove(role)
            self._changeColor(role, self._okColor)
        # Checking against equality of IPs of the same version...
        if self._bothIpsEqual(role):
            self._errs.sameVers.add(_mpRoleVer[role])
            self._changeBothColor(role, self._errColor)
        elif _mpRoleVer[role] in self._errs.sameVers:
            self._errs.sameVers.remove(_mpRoleVer[role])
            self._changeBothColor(role, self._okColor)
        self._updateErrMsgOkBtn()
        return True
    
    def _allIpsEmpty(self) -> bool:
        return not any(
            self._ipsData[idx].svar.get()
            for idx in self._ipsData.keys())
    
    def _bothIpsEqual(self, role: IPRole) -> bool:
        if role == IPRole.PRIM_4 or role == IPRole.SECON_4:
            return self._ipsData[IPRole.PRIM_4].ip is not None and \
                self._ipsData[IPRole.SECON_4].ip is not None and \
                self._ipsData[IPRole.PRIM_4].ip == self._ipsData[
                IPRole.SECON_4].ip
        elif role == IPRole.PRIM_6 or role == IPRole.SECON_6:
            return self._ipsData[IPRole.PRIM_6].ip is not None and \
                self._ipsData[IPRole.SECON_6].ip is not None and \
                self._ipsData[IPRole.PRIM_6].ip == self._ipsData[
                IPRole.SECON_6].ip
    
    def _changeAllColors(self, color: str) -> None:
        for ipIdx in self._ipsData.keys():
            self._ipsData[ipIdx].lbl.config(foreground=color)
    
    def _changeBothColor(self, idx: IPRole, color: str) -> None:
        if idx == IPRole.PRIM_4 or idx == IPRole.SECON_4:
            self._ipsData[IPRole.PRIM_4].lbl.config(foreground=color)
            self._ipsData[IPRole.SECON_4].lbl.config(foreground=color)
        elif idx == IPRole.PRIM_6 or idx == IPRole.SECON_6:
            self._ipsData[IPRole.PRIM_6].lbl.config(foreground=color)
            self._ipsData[IPRole.SECON_6].lbl.config(foreground=color)
    
    def _chnagePeerColor(self, role: IPRole, color: str) -> None:
        """Changes the color of the other IP in the same version."""
        match role:
            case IPRole.PRIM_4:
                self._ipsData[IPRole.SECON_4].lbl.config(foreground=color)
            case IPRole.SECON_4:
                self._ipsData[IPRole.PRIM_4].lbl.config(foreground=color)
            case IPRole.PRIM_6:
                self._ipsData[IPRole.SECON_6].lbl.config(foreground=color)
            case IPRole.SECON_6:
                self._ipsData[IPRole.PRIM_6].lbl.config(foreground=color)
    
    def _changeColor(self, ip_idx: IPRole, color: str) -> None:
        self._ipsData[ip_idx].lbl.config(foreground=color)
    
    def _updateErrMsgOkBtn(self) -> None:
        """Updates error messages and OK button enability."""
        msgs = list[str]()
        #
        if self._errs.nameErr != _DnsNameErrs.OK:
            msgs.append(_NAME_MSGS[self._errs.nameErr])
        #
        if self._errs.noIp:
            msgs.append(_('ALL_IPS_EMPTY'))
        #
        for role in self._errs.dupIps:
            msgs.append(_('DUP_DNS_IP').format(
                _(_mpRoleMoid[role]),
                self._mpIpDns[self._ipsData[role].ip].name)) # type: ignore
        #
        for role in self._errs.badIps:
            msgs.append(_('BAD_DNS_IP').format(_(_mpRoleMoid[role])))
        #
        for ver in self._errs.sameVers:
            msgs.append(_('SAME_PRIM_SECON').format(_mpVerMoid[ver]))
        #
        msg = '\n'.join(msgs)
        self._txt.config(state=tk.NORMAL)
        self._txt.delete("1.0", tk.END)
        self._txt.insert(tk.END, msg)
        self._txt.config(state=tk.DISABLED)
        if msgs:
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
