#
# 
#

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, MutableSequence, TYPE_CHECKING

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
            primary_col_width: int = 100,
            secondary_col_width: int = 100,
            **kwargs
            ) -> None:
        super().__init__(master, **kwargs)
        self._NAME_COL_IDX = 0
        self._PRIM_COL_IDX = 1
        self._SECON_COL_IDX = 2
        self._cbDoubleClicked = double_clicked_cb
        """The callback to be called if an item is double clicked."""
        self._idxIid: dict[int, str] = {}
        """The mapping between index and iid of the items in the view."""
        self._iidIdx: dict[str, int] = {}
        """The mapping between iid and index of the items in the view."""
        self._initGui(
            name_col_width,
            primary_col_width,
            secondary_col_width)
        # Bindings...
        self._trvw.bind('<Double-1>', self._onItemDoubleClicked)
    
    def _onItemDoubleClicked(self, event: tk.Event) -> None:
        iid = self._trvw.identify_row(event.y)
        if iid and self._cbDoubleClicked:
            self._cbDoubleClicked()
    
    def _initGui(
            self,
            name_col_width: int,
            primary_col_width: int,
            secondary_col_width: int,
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
            self._PRIM_COL_IDX,
            self._SECON_COL_IDX,))
        self._trvw.column('#0', width=0, stretch=tk.NO)  # Hidden column for tree structure
        self._trvw.column(
            self._NAME_COL_IDX,
            anchor=tk.W,
            width=name_col_width,
            stretch=False)
        self._trvw.column(
            self._PRIM_COL_IDX,
            anchor=tk.W,
            width=primary_col_width,
            stretch=False)
        self._trvw.column(
            self._SECON_COL_IDX,
            anchor=tk.W,
            width=secondary_col_width,
            stretch=False)
        # Create column headings
        self._trvw.heading('#0', text='', anchor=tk.W)  # Hidden heading for tree structure
        self._trvw.heading(self._NAME_COL_IDX, text=_('NAME'), anchor=tk.W)
        self._trvw.heading(self._PRIM_COL_IDX, text=_('PRIMARY'), anchor=tk.W)
        self._trvw.heading(
            self._SECON_COL_IDX,
            text=_('SECONDARY'),
            anchor=tk.W)
    
    def _dnsToValues(self, dns: DnsServer) -> tuple[str, str, str]:
        return (
            dns.name,
            str(dns.primary),
            '' if dns.secondary is None else str(dns.secondary))
    
    def clear(self) -> None:
        """Clears all DNS servers from the View."""
        for child in self._trvw.get_children():
            self._trvw.delete(child)
        self._iidIdx.clear()
        self._idxIid.clear()
    
    def getColsWidth(self) -> tuple[int, int, int]:
        """Returns the width of `Name`, `Primary`, and `Secondary` columns
        respectively.
        """
        colsWidth = list[int]()
        colsWidth.append(self._trvw.column(self._NAME_COL_IDX, 'width'))
        colsWidth.append(self._trvw.column(self._PRIM_COL_IDX, 'width'))
        colsWidth.append(self._trvw.column(self._SECON_COL_IDX, 'width'))
        return tuple(colsWidth) # type: ignore
    
    def getSetectedIdx(self) -> int | None:
        """Gets the zero-based index of the selected DNS server in the
        View. If nothing is selected, it returns `None`.
        """
        selection = self._trvw.selection()
        match len(selection):
            case 0:
                return None
            case 1:
                return self._iidIdx[selection[0]]
            case _:
                logging.error(
                    'more than one item in the Dnsview is selected',
                    stack_info=True,)
    
    def populate(self, dnses: MutableSequence[DnsServer]) -> None:
        self.clear()
        for idx, dns in enumerate(dnses):
            iid = self._trvw.insert(
                parent='',
                index=tk.END,
                values=self._dnsToValues(dns))
            self._iidIdx[iid] = idx
            self._idxIid[idx] = iid
    
    def appendDns(self, dns: DnsServer) -> None:
        idx = len(self._idxIid)
        iid = self._trvw.insert(
            parent='',
            index=tk.END,
            values=self._dnsToValues(dns))
        self._idxIid[idx] = iid
        self._iidIdx[iid] = idx
    
    def deleteIdx(self, idx: int) -> None:
        iid = self._idxIid[idx]
        self._trvw.delete(iid)
        del self._idxIid[idx]
        del self._iidIdx[iid]
    
    def changeDns(self, idx: int, dns: DnsServer) -> None:
        iid = self._idxIid[idx]
        self._trvw.item(iid, values=self._dnsToValues(dns))
