#
# 
#

import enum
from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, TYPE_CHECKING, Mapping, NamedTuple

from db import DnsServer, IPRole
from ntwrk import NetAdap, NetConfig
from utils.keyboard import Modifiers


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
    """This class represents a matrix of widgets. The typical using
    scenario is to save widgets in a matrix of `dict[_CR, ttk.Widget]`,
    calling `update` or `update_idealtasks` and then assign the matrix
    to the `matric` property of this class.
    """
    def __init__(self, widgets: Mapping[_CR, ttk.Widget]) -> None:
        self._nRows: int
        self._nCols: int
        self._wmax: dict[int, int]
        self._hmax: dict[int, int]
        self._x: tuple[int, ...]
        self._y: tuple[int, ...]
        self._calculate(widgets)
    
    @property
    def nRows(self) -> int:
        """Gets the number of rows of widgets."""
        return self._nRows
    
    @property
    def nCols(self) -> int:
        """Gets the number of columns of widgets."""
        return self._nCols
    
    def widthof(self, col: int) -> int:
        """Gets the width of specified column. It might raise `KeyError`."""
        return self._wmax.get(col, 0)
    
    def heightof(self, row: int) -> int:
        """Gets the height of specified row. It might raise `KeyError`."""
        return self._hmax.get(row, 0)
    
    def totalWidth(self) -> int:
        """Returns the total width of the matrix."""
        return self._x[self._nCols]
    
    def totalHeight(self) -> int:
        """Returns the total width of the matrix."""
        return self._y[self._nRows]
    
    def xof(self, col: int) -> int:
        """Gets the x-coordinate of specified column. It might raise
        `ValueError`, `TypeError`, or `KeyError`.
        """
        return self._x[col]
    
    def yof(self, row: int) -> int:
        """Gets the y-coordinate of specified row. It might raise
        `ValueError`, `TypeError`, or `KeyError`.
        """
        return self._y[row]
    
    def _calculate(self, widgets: Mapping[_CR, ttk.Widget]) -> None:
        from collections import defaultdict
        ccrs = defaultdict[int, list[_CR]](list)
        rcrs = defaultdict[int, list[_CR]](list)
        for cr in widgets:
            ccrs[cr.col].append(cr)
            rcrs[cr.row].append(cr)
        # Calculating `nCols`...
        try:
            self._nCols = max(ccrs.keys()) + 1
        except ValueError:
            self._nCols = 0
        # Calculating `nRows`...
        try:
            self._nRows = max(rcrs.keys()) + 1
        except ValueError:
            self._nRows = 0
        # Calculating `_wmax`...
        self._wmax = {
            col:max(widgets[cr].winfo_width() for cr in ccrs[col])
            for col in ccrs}
        # Calculating `_hmax`...
        self._hmax = {
            row:max(widgets[cr].winfo_height() for cr in rcrs[row])
            for row in rcrs}
        # Calculating `_x`...
        x = [0]
        value = 0
        for idx in range(self._nCols):
            value += self._wmax.get(idx, 0)
            x.append(value)
        self._x = tuple(x)
        # Calculating `_y`...
        y = [0]
        value = 0
        for idx in range(self._nRows):
            value += self._hmax.get(idx, 0)
            y.append(value)
        self._y = tuple(y)


class IpsView(ttk.Frame):
    def __init__(
            self,
            master: tk.Misc | None = None,
            *,
            line_space: int = 3,
            line_width = 1,
            ) -> None:
        super().__init__(master)
        self._sLine = line_space
        """The spacing between lines."""
        self._wLine = line_width
        """The width of lines."""
        self._width = 0
        """The width of the canvas."""
        self._height = 0
        """The height of the canvas."""
        self._selection = list[int]()
        """The list of all selected IPs index."""
        self._mode = _RedrawMode.NONE
        self._ips = list[IPv4 | IPv6]()
        self._nmRoles = list[tuple[str, tuple[IPRole | None, ...]]]()
        self._msg: str = ''
        self._mpCrLbl = dict[_CR, ttk.Label]()
        """The between matrix positions and labels:
        
        `_CR(column, row) -> ttk,Label`
        """
        self._mpLblCr = dict[ttk.Label, _CR]()
        """The between labels andmatrix positions:
        
        `ttk,Label -> _CR(column, row)`
        """
        self._initGui()
        self._defaultClr = self._cnvs.cget('background')
        self._selectedClr = 'lightblue'
        # Binding events...
        self._cnvs.bind('<Configure>', self._onSizeChanged)
        self._cnvs.bind('<Button-1>', self._onCnvsClicked)
    
    def _onSizeChanged(self, event: tk.Event) -> None:
        if event.width != self._width or event.height != self._height:
            self._width = event.width
            self._height = event.height
            if self._mode == _RedrawMode.MSG:
                self._redrawMsg()
    
    def _onCnvsClicked(self, _: tk.Event) -> None:
        if self._mode != _RedrawMode.IPS:
            return
        self.deselect()
    
    def _onLblClicked(self, event: tk.Event) -> None:
        if isinstance(event.state, str):
            logging.error('The event.state is str')
            return
        idx = self._mpLblCr[event.widget].row - 1
        if (event.state & Modifiers.CONTROL) == Modifiers.CONTROL:
            if idx in self._selection:
                self.delSeltIdx(idx)
            else:
                self.addSelIdx(idx)
        else:
            self.deselect()
            self.addSelIdx(idx)
    
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
            borderwidth=0,
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
    
    def clear(self) -> None:
        self._mode = _RedrawMode.NONE
        self._selection.clear()
        self._mpCrLbl.clear()
        self._cnvs.delete('all')
        self._msg = ''
        self._ips.clear()
        self._nmRoles.clear()

    def populate(
            self,
            net_item: NetAdap | NetConfig,
            dnses: Iterable[DnsServer],
            ) -> None:
        self.clear()
        if isinstance(net_item, NetAdap):
            nConfigs = len(net_item.Configs)
            if nConfigs == 1:
                config = net_item.Configs[0]
        elif isinstance(net_item, NetConfig):
            nConfigs = 1
            config = net_item
        else:
            raise TypeError(
                'expected NetAdap or NetConfig but got '
                f'{net_item.__class__.__qualname__}')
        #
        if nConfigs > 1:
            self._mode = _RedrawMode.MSG
            self._msg = _('MANY_ADAP_CONFIGS')
        elif nConfigs == 0:
            self._mode = _RedrawMode.MSG
            self._msg = _('NO_ADAP_CONFIG')
        else:
            if config.DNSServerSearchOrder is not None: # type: ignore
                self._mode = _RedrawMode.IPS
                self._populateTable(config, dnses) # type: ignore
            else:
                self._mode = _RedrawMode.MSG
                if  net_item.dhcpAccess():
                    self._msg = _('NET_ADAP_DHCP')
                else:
                    self._msg = _('NO_DHCP_NO_DNS')
        self._redraw()
    
    def _populateTable(
            self,
            net_config: NetConfig,
            dnses: Iterable[DnsServer],
            ) -> None:
        """Populates the IP table in IPs mode."""
        self._ips.clear()
        self._nmRoles.clear()
        ips = net_config.DNSServerSearchOrder
        if not ips:
            # `ips` is either `None` or empty...
            self._redrawRoles()
        else:
            self._ips = list(ips)
            for dns in dnses:
                roles = [dns.getRole(ip) for ip in ips]
                if any(roles):
                    self._nmRoles.append((dns.name, tuple(roles),))
            self._nmRoles.sort(key=lambda x: len(x[1]))
    
    def _redraw(self) -> None:
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
            justify='center',
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
        # Clearing the canvas...
        self._cnvs.delete('all')
        self._mpCrLbl.clear()
        # Creating labels outside visible boundaries...
        x = self._getCnvsWidth() + 2
        y = self._getCnvsHeight() + 2
        for row, ip in enumerate(self._ips, 1):
            cr = _CR(0, row)
            lbl = ttk.Label(self._cnvs, cursor='hand2', text=str(ip))
            lbl.bind('<Button-1>', self._onLblClicked)
            lbl.place(x=x, y=y)
            self._mpCrLbl[cr] = lbl
            self._mpLblCr[lbl] = cr
        for col, mnRoles in enumerate(self._nmRoles, 1):
            cr = _CR(col, 0)
            lbl = ttk.Label(self._cnvs, text=mnRoles[0])
            lbl.bind('<Button-1>', self._onCnvsClicked)
            lbl.place(x=x, y=y)
            self._mpCrLbl[cr] = lbl
            self._mpLblCr[lbl] = cr
            for row, role in enumerate(mnRoles[1], 1):
                if role is not None:
                    cr = _CR(col, row)
                    lbl = ttk.Label(
                        self._cnvs,
                        cursor='hand2',
                        text=self._roleToStr(role))
                    lbl.bind('<Button-1>', self._onLblClicked)
                    lbl.place(x=x, y=y)
                    self._mpCrLbl[cr] = lbl
                    self._mpLblCr[lbl] = cr
            self._mpLblCr[lbl] = cr
        self.update_idletasks()
        widtrix = Widtrix(self._mpCrLbl)
        # Darwing labels...
        for col in range(widtrix.nCols):
            for row in range(widtrix.nRows):
                cr = _CR(col, row)
                try:
                    lbl = self._mpCrLbl[cr]
                except KeyError:
                    continue
                x = widtrix.xof(cr.col) + (2 * (cr.col + 1) * self._sLine) + \
                    (cr.col * self._wLine) + (widtrix.widthof(cr.col) // 2)
                y = widtrix.yof(cr.row) + (2 * (cr.row + 1) * self._sLine) + \
                    (cr.row * self._wLine)
                self._cnvs.create_window(
                    x,
                    y,
                    window=lbl,
                    anchor='n')
        # Drawing horizontal lines...
        if widtrix.nCols > 1:
            lineWidth = widtrix.totalWidth() + (widtrix.nCols - 1) * (
                2 * self._sLine + self._wLine)
        else:
            lineWidth = widtrix.totalWidth() + 20
        x0 = 2 * self._sLine + self._sLine
        y0 = (3 * self._sLine) + self._wLine + widtrix.yof(1)
        self._cnvs.create_line(
            x0,
            y0,
            lineWidth + self._sLine,
            y0,
            width=self._wLine)
        for idx in range(2, widtrix.nRows):
            y0 = (2 * idx + 1) * self._sLine + (idx * self._wLine) \
                + widtrix.yof(idx)
            self._cnvs.create_line(
                x0,
                y0,
                lineWidth + self._sLine,
                y0,
                dash=(3, 3,),
                width=self._wLine)
        # Drawing vertical lines...
        lineWidth = widtrix.totalHeight() + (widtrix.nRows - 1) * (2 *
            self._sLine + self._wLine)
        x0 = (3 * self._sLine) + self._wLine + widtrix.xof(1)
        y0 = 2 * self._sLine + self._sLine
        self._cnvs.create_line(
            x0,
            y0,
            x0,
            lineWidth + self._sLine,
            width=self._wLine)
        for idx in range(2, widtrix.nCols):
            x0 = (2 * idx + 1) * self._sLine + (idx * self._wLine) \
                + widtrix.xof(idx)
            self._cnvs.create_line(
                x0,
                y0,
                x0,
                lineWidth + self._sLine,
                dash=(3, 3,),
                width=self._wLine)
        # Setting `scrollregion`...
        scrlWidth = widtrix.totalWidth() + (widtrix.nCols + 1) * (
            2 * self._sLine + self._wLine)
        scrlHeight = widtrix.totalHeight() + (widtrix.nRows + 1) * (
            2 * self._sLine + self._wLine)
        self._cnvs.config(scrollregion=(
            0,
            0,
            scrlWidth,
            scrlHeight,))
    
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
        bd = max([2, int(self._cnvs.cget('borderwidth')),])
        return self._cnvs.winfo_width() - (2 * bd)
    
    def _getCnvsHeight(self) -> int:
        bd = max([2, int(self._cnvs.cget('borderwidth')),])
        return self._cnvs.winfo_height() - (2 * bd)
    
    def deselect(self) -> None:
        """Deselects all the selected IPs if any."""
        for idx in self._selection.copy():
            self.delSeltIdx(idx)

    def addSelIdx(self, idx: int) -> None:
        """Adds the IPs with `idx` index to the selection."""
        self._mpCrLbl[_CR(0, idx + 1)].config(background=self._selectedClr)
        self._selection.append(idx)

    def delSeltIdx(self, idx: int) -> None:
        """Deletes the IPs with `idx` index from the selection."""
        try:
            self._selection.remove(idx)
        except ValueError:
            return
        self._mpCrLbl[_CR(0, idx + 1)].config(background=self._defaultClr)

    def getSelectedIndicies(self) -> tuple[int, ...]:
        return tuple(self._selection)
    
    def getSelectedIps(self) -> tuple[IPv4 | IPv6, ...]:
        return tuple([self._ips[idx] for idx in self.getSelectedIndicies()])
