#
# 
#

import enum
import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from ntwrk import ACIdx, AdapCfgBag, NetAdap, ConnStatus, NetConfig
from utils.types import TkImg


if TYPE_CHECKING:
    _: Callable[[str], str]


class _ConnFlags(enum.IntFlag):
    NO_FLAGS = 0X0
    NTWRK = 0X1
    INET = 0X2


class NetAdapView(tk.Frame):
    def __init__(
            self,
            master: tk.Misc,
            selection_cb: Callable[[ACIdx | None], None] | \
                None = None,
            d_click_cb: Callable[[], None] | None = None,
            *,
            name_col_width: int = 200,
            gntwrk_img: TkImg,
            rntwrk_img: TkImg,
            ginet_img: TkImg,
            rinet_img: TkImg,
            **kwargs,
            ) -> None:
        super().__init__(master, **kwargs)
        self._cbSelection = selection_cb
        self._cbDClick = d_click_cb
        self._connColor = 'green'
        self._disconnColor = '#ca482e'
        self._imgs: dict[int, TkImg] = {
            0: rntwrk_img,
            1: gntwrk_img,
            2: rinet_img,
            3: ginet_img,}
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
        self._trvw.column('#0', width=40, stretch=tk.NO)  # Hidden column for tree structure
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
    
    def clear(self) -> None:
        self._mpIidIdx.clear()
        self._mpIdxIid.clear()
        for child in self._trvw.get_children(''):
            self._trvw.delete(child)
    
    def populate(self, bag: AdapCfgBag) -> None:
        self.clear()
        for adapIdx, adap in bag.iterAdaps():
            self.addAdap(adap, adapIdx)
            for configIdx, config in bag.iterConfigs(adapIdx):
                self.addConfig(adapIdx, config, configIdx)
    
    def getSelectedIdx(self) -> ACIdx | None:
        """Gets the index of selected item, either a network adapter or
        network adapter configuration.
        """
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

    def _iidToAcidx(self, iid: str) -> ACIdx | None:
        try:
            return self._mpIidIdx[iid]
        except KeyError:
            pass
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
    
    def _acidxToIid(self, idx: ACIdx) -> str:
        try:
            return self._mpIdxIid[idx]
        except KeyError:
            pass
        return str(idx.adapIdx) if idx.cfgIdx is None else \
            f'{idx.adapIdx}-{idx.cfgIdx}'
    
    def _getImg(self, adap: NetAdap) -> TkImg:
        flags = _ConnFlags.NO_FLAGS
        if adap.NetConnectionStatus == ConnStatus.CONNECTED:
            flags |= _ConnFlags.NTWRK
        if adap.connectivity():
            flags |= _ConnFlags.INET
        return self._imgs[flags]
    
    def addAdap(self, adap: NetAdap, adap_idx: ACIdx) -> None:
        proposedIid = self._acidxToIid(adap_idx)
        iid = self._trvw.insert(
            parent='',
            index=tk.END,
            iid=proposedIid,
            image=self._getImg(adap), # type: ignore
            values=(adap.NetConnectionID,),)
        if iid != proposedIid:
            self._mpIdxIid[adap_idx] = iid
            self._mpIidIdx[iid] = adap_idx
    
    def addConfig(
            self,
            adap_idx: ACIdx,
            config: NetConfig,
            config_idx: ACIdx,
            ) -> None:
        proposedIid = self._acidxToIid(config_idx)
        iid = self._trvw.insert(
            parent=self._acidxToIid(adap_idx),
            index=tk.END,
            iid=proposedIid,
            values=(config.Index,),)
        if iid != proposedIid:
            self._mpIdxIid[adap_idx] = iid
            self._mpIidIdx[iid] = adap_idx
    
    def delItem(self, idx: ACIdx) -> None:
        """Deletes the specified item, either NetAdap or NetConfig, from
        the widget.
        """
        iid = self._acidxToIid(idx)
        self._trvw.delete(iid)
        del self._mpIdxIid[idx]
        del self._mpIidIdx[iid]

    def changeAdap(self, adap: NetAdap, adap_idx: ACIdx) -> None:
        iid = self._acidxToIid(adap_idx)
        self._trvw.item(iid, image=self._getImg(adap)) # type: ignore
        self._trvw.item(iid, values=(adap.NetConnectionID,))

    def changeConfig(self, config: NetConfig, config_idx: ACIdx) -> None:
        iid = self._acidxToIid(config_idx)
        self._trvw.item(iid, values=(config.Index,))
