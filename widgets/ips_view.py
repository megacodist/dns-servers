#
# 
#

import enum
from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, TYPE_CHECKING, NamedTuple

from db import DnsServer, IPRole
from ntwrk import NetInt


if TYPE_CHECKING:
    _: Callable[[str], str]


class _RedrawMode(enum.IntEnum):
    NONE = 0
    MSG = 1
    IPS = 2


class _CR(NamedTuple):
    col: int
    row: int

    def __repr__(self):
        return f"CR(column={self.col}, row={self.row})"


class Widtrix:
    def __init__(self) -> None:
        self._nRows: int = 0
        self._nCols: int = 0
        self._widgets = dict[_CR, ttk.Widget]()
    
    @property
    def nRows(self) -> int:
        return self._nRows
    
    @property
    def nCols(self) -> int:
        return self._nCols
    
    def 


class IpsView(ttk.Frame):
    def __init__(
            self,
            master: tk.Misc | None = None,
            *,
            foo: str = '',
            ) -> None:
        super().__init__(master)
        self._mode = _RedrawMode.NONE
        self._ips: Iterable[IPv4 | IPv6] = tuple()
        self._nmRoles: Iterable[tuple[str, tuple[IPRole | None, ...]]] = tuple()
        self._msg = ''
        self._initGui()
    
    def _initGui(self) -> None:
        #
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        #
        self._vscrlbr = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL)
        self._hscrlbr = ttk.Scrollbar(
            self,
            orient=tk.HORIZONTAL)
        self._cnvs = tk.Canvas(
            self,
            bd=0,
            xscrollcommand=self._hscrlbr.set,
            yscrollcommand=self._vscrlbr.set)  
        self._vscrlbr['command'] = self._cnvs.yview
        self._hscrlbr['command'] = self._cnvs.xview
        self._cnvs.grid(
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
    
    def populate(self, net_int: NetInt, dnses: Iterable[DnsServer]) -> None:
        if net_int.dnsProvided():
            self._mode = _RedrawMode.IPS
            ips = net_int.DNSServerSearchOrder
            if not ips:
                # `ips` is either `None` or empty...
                self._ips = tuple()
                self._redrawRoles()
            else:
                self._ips = ips
                nmRoles = list[tuple[str, tuple[IPRole | None, ...]]]()
                for dns in dnses:
                    roles = [dns.getRole(ip) for ip in ips]
                    if any(roles):
                        nmRoles.append((dns.name, tuple(roles),))
                nmRoles.sort(key=lambda x: len(x[1]))
                self._nmRoles = nmRoles
                self._redrawRoles()
        else:
            self._mode = _RedrawMode.MSG
            if  net_int.dhcpAccess():
                self._msg = _('NET_INT_DHCP')
                self._redrawMsg()
            else:
                self._msg = _('NO_DHCP_NO_DNS')
                self._redrawMsg()
    
    def _Redraw(self) -> None:
        if self._mode == _RedrawMode.MSG:
            self._redrawMsg()
        elif self._mode == _RedrawMode.IPS:
            self._redrawRoles()
    
    def _redrawMsg(self) -> None:
        self._cnvs.delete('all')
        cnvsWidth = self._getCnvsWidth()
        cnvsHeight = self._getCnvsHeight()
        msgWidth = int(cnvsWidth * 0.8)
        msg = tk.Message(
            self._cnvs,
            text=self._msg,
            width=msgWidth,)
        self.update_idletasks()
        msgHeight = msg.winfo_height()
        if msgHeight > cnvsHeight:
            msgWidth = cnvsWidth
            msg.config(width=msgWidth)
            msg.config(text=self._msg)
            self._cnvs.create_window(0, 0, window=msg)
            self.update_idletasks()
            self._cnvs.config(scrollregion=(
                0,
                0,
                cnvsWidth,
                msg.winfo_height(),))
        else:
            self._cnvs.create_window(
                cnvsWidth / 2,
                cnvsHeight / 2,
                window=msg,
                anchor='center')
            self._cnvs.config(scrollregion=(
                0,
                0,
                cnvsWidth,
                cnvsHeight,))

    def _redrawRoles(self) -> None:
        self._cnvs.delete('all')
        lblIps = [ttk.Label(self._cnvs, text=str(ip)) for ip in self._ips]
        lblHeads = [
            ttk.Label(self._cnvs, text='\n'.join(tpl[0].split()))
            for tpl in self._nmRoles]
        self.update_idletasks()
        maxIpsWidth = max(lbl.winfo_width() for lbl in lblIps)
        maxHeadsWidth = max(lbl.winfo_height() for lbl in lblHeads)
        #
        lbl = tk.Label(self._frm, bitmap='gray50')
        lbl.grid(column=0, row=0, sticky=tk.NSEW)
        #
        for idx, ip in enumerate(self._ips, 1):
            lbl = ttk.Label(self._frm, text=str(ip))
            lbl.grid(column=0, row=idx)
        #
        for j, tpl in enumerate(self._nmRoles, 1):
            lbl = ttk.Label(self._frm, text=tpl[0])
            lbl.grid(column=j, row=0)
            for i, role in enumerate(tpl[1], 1):
                lbl = ttk.Label(self._frm, text=self._roleToStr(role))
                lbl.grid(column=j, row=i)
        #
        self._cnvs.create_window(10, 10, anchor="nw", window=self._frm)
        self._cnvs.config(scrollregion=(
            0,
            0,
            self._frm.winfo_width(),
            self._frm.winfo_height()))
    
    def _roleToStr(self, role: IPRole | None) -> str:
        match role:
            case IPRole.PRIM_4:
                return 'P-4'
            case IPRole.SECON_4:
                return 'S-4'
            case IPRole.PRIM_6:
                return 'P-6'
            case IPRole.SECON_6:
                return 'S-6'
            case None:
                return ''
    
    def _getCnvsWidth(self) -> int:
        return self._cnvs.winfo_width() - (2 * int(self._cnvs.cget('bd')))
    
    def _getCnvsHeight(self) -> int:
        return self._cnvs.winfo_height() - (2 * int(self._cnvs.cget('bd')))
    
    def clear(self) -> None:
        self._mode = _RedrawMode.NONE
        self._cnvs.delete('all')
