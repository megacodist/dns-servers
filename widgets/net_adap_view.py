#
# 
#

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, TYPE_CHECKING

from ntwrk import ACIdx, NetAdap, ConnStatus


if TYPE_CHECKING:
    _: Callable[[str], str]


class NetAdapView(tk.Frame):
    def __init__(
            self,
            master: tk.Misc,
            selection_cb: Callable[[ACIdx | None], None] | \
                None = None,
            d_click_cb: Callable[[], None] | None = None,
            *,
            name_col_width: int = 200,
            **kwargs,
            ) -> None:
        super().__init__(master, **kwargs)
        self._cbSelection = selection_cb
        self._cbDClick = d_click_cb
        self._connColor = 'green'
        self._disconnColor = '#ca482e'
        self._mpIidIdx = dict[str, ACIdx]()
        self._mpIdxIid = dict[ACIdx, str]()
        self._NAME_COL_IDX = 1
        self._initGui(name_col_width)
        # Bindings...
        self._trvw.bind("<<TreeviewSelect>>", self._onSelection)
        self._trvw.bind('<Double-1>', self._onDoubleClicked)
    
    def _initGui(self, name_col_width: int) -> None:
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
            selectmode='browse',
            xscrollcommand=self._hscrlbr.set,
            yscrollcommand=self._vscrlbr.set)  
        self._vscrlbr.config(command=self._trvw.yview)
        self._hscrlbr.config(command=self._trvw.xview)
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
        self._trvw.config(columns=(self._NAME_COL_IDX,))
        self._trvw.column('#0', width=20, stretch=tk.NO)  # Hidden column for tree structure
        self._trvw.column(
            self._NAME_COL_IDX,
            anchor=tk.W,
            width=name_col_width,
            stretch=False)
        # Create column headings
        self._trvw.heading('#0', text='', anchor=tk.W)  # Hidden heading for tree structure
        self._trvw.heading(self._NAME_COL_IDX, text=_('NAME'), anchor=tk.W)
    
    def _onSelection(self, _: tk.Event) -> None:
        selection = self.getSelectedIdx()
        if self._cbSelection:
            self._cbSelection(selection)
    
    def _onDoubleClicked(self, _: tk.Event) -> None:
        if self._cbDClick:
            self._cbDClick()
    
    def _getItemColor(self, net_adap: NetAdap) -> str:
        if net_adap.NetConnectionStatus == ConnStatus.CONNECTED:
            return self._connColor
        else:
            return self._disconnColor

    def populate(self, net_adaps: Iterable[NetAdap]) -> None:
        self.clear()
        for adapIdx, adap in enumerate(net_adaps):
            sAdapIdx = str(adapIdx)
            sAdapIid = self._trvw.insert(
                parent='',
                index=tk.END,
                iid=sAdapIdx,
                values=(adap.NetConnectionID,)) # type: ignore
            if sAdapIdx != sAdapIid:
                self._mpIidIdx[sAdapIid] = ACIdx(adapIdx, None,)
            #
            for configIdx, config in enumerate(adap.Configs):
                sConfigIdx = f'{sAdapIid}-{configIdx}'
                sConfigIid = self._trvw.insert(
                    parent=sAdapIid,
                    index=tk.END,
                    iid=sConfigIdx,
                    values=(str(config.Index),))
                if sConfigIid != sConfigIdx:
                    self._mpIidIdx[sConfigIid] = ACIdx(adapIdx, configIdx)
    
    def clear(self) -> None:
        self._mpIidIdx.clear()
        for child in self._trvw.get_children(''):
            self._trvw.delete(child)
    
    def getSelectedIdx(self) -> ACIdx | None:
        """Gets the index of selected interface."""
        selection = self._trvw.selection()
        match len(selection):
            case 0:
                return None
            case 1:
                iid = selection[0]
                try:
                    return self._mpIidIdx[iid]
                except KeyError:
                    return self._iidToAcidx(iid)
            case _:
                logging.error(
                    'more than one item in the Dnsview is selected',
                    stack_info=True,)
    
    def _acidxToStr(self, idx: ACIdx) -> str:
        return str(idx.adapIdx) if idx.cfgIdx is None else \
            f'{idx.adapIdx}-{idx.cfgIdx}'

    def _iidToAcidx(self, iid: str) -> ACIdx | None:
        parts = iid.split('-')
        match len(parts):
            case 1:
                return ACIdx(int(parts[0]), None,)
            case 2:
                return ACIdx(int(parts[0]), int(parts[1]),)
            case _:
                logging.error(
                    'invalid number of dash-separated parts of iid',
                    stack_info=True,)
    
    def addAdap(self, adap: NetAdap, adap_idx: ACIdx) -> None:
        iid = self._trvw.insert(
            parent='')
