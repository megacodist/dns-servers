#
# 
#

from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, TYPE_CHECKING

from db import DnsServer, IPRole
from ntwrk import NetInt


if TYPE_CHECKING:
    _: Callable[[str], str]


class IpsView(ttk.Frame):
    def __init__(
            self,
            master: tk.Misc | None = None,
            *,
            foo: str = '',
            ) -> None:
        super().__init__(master)
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
        #
        self._frm = ttk.Frame(self._cnvs)
    
    def populate(self, net_int: NetInt, dnses: Iterable[DnsServer]) -> None:
        self.clear()
        if net_int.dhcpEnabled():
            self._showDhcp()
        else:
            ips = net_int.DNSServerSearchOrder
            if ips is None:
                self._showIpsRoles(tuple(), tuple())
            else:
                res = list[tuple[str, tuple[IPRole | None, ...]]]()
                for dns in dnses:
                    roles = [dns.getRole(ip) for ip in ips]
                    if any(roles):
                        res.append((dns.name, tuple(roles),))
                self._showIpsRoles(ips, res)
    
    def _showDhcp(self) -> None:
        self.clear()
        msg = tk.Message(
            self._frm,
            text=_('NET_INT_DHCP'),
            width=self._frm.winfo_width())
        msg.pack(fill=tk.BOTH, expand=True)
        self._cnvs.config(scrollregion=(
            0,
            0,
            self._frm.winfo_width(),
            self._frm.winfo_height()))

    def _showIpsRoles(
            self,
            ips: Iterable[IPv4 | IPv6],
            roles: Iterable[tuple[str, tuple[IPRole | None, ...]]],
            ) -> None:
        self.clear()
        #
        lbl = tk.Label(self._frm, bitmap='warning')
        #
        for idx, ip in enumerate(ips, 1):
            lbl = ttk.Label(self._frm, text=str(ip))
            lbl.grid(column=0, row=idx)
        #
        for j, tpl in enumerate(roles, 1):
            lbl = ttk.Label(self._frm, text=tpl[0])
            lbl.grid(column=j, row=0)
            for i, role in enumerate(tpl[1], 1):
                lbl = ttk.Label(self._frm, text=self._roleToStr(role))
                lbl.grid(column=j, row=1)
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
    
    def clear(self) -> None:
        self._cnvs.delete('all')
        for widget in self._frm.winfo_children():
            widget.destroy()
        self._frm.pack(fill=tk.BOTH, expand=True)
