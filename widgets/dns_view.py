#
# 
#

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, MutableSequence, TYPE_CHECKING

from db import DnsServer


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


class Dnsview(tk.Frame):
    def __init__(
            self,
            master: tk.Misc,
            double_clicked_cb: Callable[[], None] | None = None,
            *,
            name_col_width: int = 100,
            prim_4_col_width: int = 100,
            secon_4_col_width: int = 100,
            prim_6_col_width: int = 100,
            secon_6_col_width: int = 100,
            **kwargs
            ) -> None:
        super().__init__(master, **kwargs)
        self._NAME_COL_IDX = 0
        self._PRIM_4_COL_IDX = 1
        self._SECON_4_COL_IDX = 2
        self._PRIM_6_COL_IDX = 3
        self._SECON_6_COL_IDX = 4
        self._cbDoubleClicked = double_clicked_cb
        """The callback to be called if an item is double clicked."""
        self._mpNameIid: dict[str, str] = {}
        """The mapping from name to iid of the items in the view:
        `name -> iid`
        """
        self._mpIidName: dict[str, str] = {}
        """The mapping from iid to name of the items in the view:
        `iid -> name`
        """
        self._initGui(
            name_col_width,
            prim_4_col_width,
            secon_4_col_width,
            prim_6_col_width,
            secon_6_col_width)
        # Bindings...
        self._trvw.bind('<Double-1>', self._onItemDoubleClicked)
    
    def _onItemDoubleClicked(self, event: tk.Event) -> None:
        iid = self._trvw.identify_row(event.y)
        if iid and self._cbDoubleClicked:
            self._cbDoubleClicked()
    
    def _initGui(
            self,
            name_col_width: int,
            prim_4_col_width: int,
            secon_4_col_width: int,
            prim_6_col_width: int,
            secon_6_col_width: int,
            ) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        #
        self._vscrlbr = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL)
        self._hscrlbr = ttk.Scrollbar(
            self,
            orient=tk.HORIZONTAL)
        self._trvw = ttk.Treeview(
            self,
            xscrollcommand=self._hscrlbr.set,
            yscrollcommand=self._vscrlbr.set)  
        self._vscrlbr['command'] = self._trvw.yview
        self._hscrlbr['command'] = self._trvw.xview
        self._trvw.grid(
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
        # Format columns
        self._trvw.config(columns=(
            self._NAME_COL_IDX,
            self._PRIM_4_COL_IDX,
            self._SECON_4_COL_IDX,
            self._PRIM_6_COL_IDX,
            self._SECON_6_COL_IDX,))
        self._trvw.column('#0', width=0, stretch=tk.NO)  # Hidden column for tree structure
        self._trvw.column(
            self._NAME_COL_IDX,
            anchor=tk.W,
            width=name_col_width,
            stretch=False)
        self._trvw.column(
            self._PRIM_4_COL_IDX,
            anchor=tk.W,
            width=prim_4_col_width,
            stretch=False)
        self._trvw.column(
            self._SECON_4_COL_IDX,
            anchor=tk.W,
            width=secon_4_col_width,
            stretch=False)
        self._trvw.column(
            self._PRIM_6_COL_IDX,
            anchor=tk.W,
            width=prim_6_col_width,
            stretch=False)
        self._trvw.column(
            self._SECON_6_COL_IDX,
            anchor=tk.W,
            width=secon_6_col_width,
            stretch=False)
        # Create column headings
        self._trvw.heading('#0', text='', anchor=tk.W)  # Hidden heading for tree structure
        self._trvw.heading(self._NAME_COL_IDX, text=_('NAME'), anchor=tk.W)
        self._trvw.heading(self._PRIM_4_COL_IDX, text=_('PRIM_4'), anchor=tk.W)
        self._trvw.heading(
            self._SECON_4_COL_IDX,
            text=_('SECON_4'),
            anchor=tk.W)
        self._trvw.heading(self._PRIM_6_COL_IDX, text=_('PRIM_6'), anchor=tk.W)
        self._trvw.heading(
            self._SECON_6_COL_IDX,
            text=_('SECON_6'),
            anchor=tk.W)
    
    def _dnsToValues(self, dns: DnsServer) -> tuple[str, str, str, str, str]:
        return (
            dns.name,
            '' if dns.prim_4 is None else str(dns.prim_4),
            '' if dns.secon_4 is None else str(dns.secon_4),
            '' if dns.prim_6 is None else str(dns.prim_6),
            '' if dns.secon_6 is None else str(dns.secon_6))
    
    def clear(self) -> None:
        """Clears all DNS servers from the View."""
        for child in self._trvw.get_children():
            self._trvw.delete(child)
        self._mpIidName.clear()
        self._mpNameIid.clear()
    
    def getColsWidth(self) -> tuple[int, int, int, int, int]:
        """Returns the width of `name`, `prim_4`, and `secon_4`, 'prim_6',
        and 'secon_6' columns width as a 5-tuple respectively.
        """
        colsWidth = list[int]()
        colsWidth.append(self._trvw.column(self._NAME_COL_IDX, 'width'))
        colsWidth.append(self._trvw.column(self._PRIM_4_COL_IDX, 'width'))
        colsWidth.append(self._trvw.column(self._SECON_4_COL_IDX, 'width'))
        colsWidth.append(self._trvw.column(self._PRIM_6_COL_IDX, 'width'))
        colsWidth.append(self._trvw.column(self._SECON_6_COL_IDX, 'width'))
        return tuple(colsWidth) # type: ignore
    
    def getSetectedName(self) -> str | None:
        """Gets the name of the selected DNS server in the
        View. If nothing is selected, it returns `None`.
        """
        selection = self._trvw.selection()
        match len(selection):
            case 0:
                return None
            case 1:
                return self._mpIidName[selection[0]]
            case _:
                logging.error(
                    'more than one item in the Dnsview is selected',
                    stack_info=True,)
    
    def populate(self, dnses: Iterable[DnsServer]) -> None:
        self.clear()
        for dns in dnses:
            iid = self._trvw.insert(
                parent='',
                index=tk.END,
                values=self._dnsToValues(dns))
            self._mpIidName[iid] = dns.name
            self._mpNameIid[dns.name] = iid
    
    def appendDns(self, dns: DnsServer) -> None:
        iid = self._trvw.insert(
            parent='',
            index=tk.END,
            values=self._dnsToValues(dns))
        self._mpIidName[iid] = dns.name
        self._mpNameIid[dns.name] = iid
    
    def deleteName(self, name: str) -> None:
        iid = self._mpNameIid[name]
        self._trvw.delete(iid)
        del self._mpNameIid[name]
        del self._mpIidName[iid]
    
    def changeDns(self, old_name: str, new_dns: DnsServer) -> None:
        iid = self._mpNameIid[old_name]
        self._trvw.item(iid, values=self._dnsToValues(new_dns))
        self._mpIidName[iid] = new_dns.name
        del self._mpNameIid[old_name]
        self._mpNameIid[new_dns.name] = iid
