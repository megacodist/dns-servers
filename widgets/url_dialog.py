#
# 
#

from ipaddress import AddressValueError, IPv4Address
from threading import Thread
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

from db import DnsServer
from utils.types import TkImg

if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


class _HttpRes:
    def __init__(
            self,
            response: str = '',
            latency: int | None = None,
            ) -> None:
        self.response = response
        self.latency = latency


class DnsTesterThrd(Thread):
    def __init__(self) -> None:
        super().__init__(
            group=None,
            target=None,
            name='DNS tester thread',
            args=tuple(),
            kwargs=None,
            daemon=False)


class UrlDialog(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            mp_name_dns: dict[str, DnsServer],
            dns: DnsServer,
            tick_img: TkImg,
            cross_img: TkImg,
            ) -> None:
        super().__init__(master)
        self.title(_('ENTER_DNS'))
        self.resizable(False, False)
        self.grab_set()
        #
        self._result = None
        self._mpNameDns = mp_name_dns
        self._mpNameRes = {key:_HttpRes() for key in self._mpNameDns}
        self._NAME_COL_IDX = 1
        self._RES_COL_IDX = 2
        self._DELAY_COL_IDX = 3
        # Initializing the GUI...
        self._initGui()
        # Bindings...
        #self.bind('<Return>', lambda _: self._onApproved())
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
        self._result = None
        self.destroy()

    def _onCanceled(self) -> None:
        self._result = None
        self.destroy()
    
    def _initGui(self) -> None:
        #
        self._frm_container = ttk.Frame(self)
        self._frm_container.pack(
            fill=tk.BOTH,
            expand=True,)
        #
        self._frm_url = ttk.Frame(self._frm_container)
        self._frm_url.pack(side=tk.TOP, fill=tk.X, expand=True)
        #
        self._lbl_url = ttk.Label(self._frm_url, text='URL')
        self._lbl_url.pack(side=tk.LEFT)
        #
        self._entry_url = ttk.Entry(self._frm_url)
        self._entry_url.pack(fill=tk.BOTH, expand=True)
        #
        self._frm_dnses = ttk.Frame(self._frm_container)
        self._frm_dnses.columnconfigure(0, weight=1)
        self._frm_dnses.rowconfigure(0, weight=1)
        self._frm_dnses.pack(fill=tk.BOTH, expand=True)
        #
        self._vscrlbr = ttk.Scrollbar(
            self._frm_dnses,
            orient=tk.VERTICAL)
        self._hscrlbr = ttk.Scrollbar(
            self._frm_dnses,
            orient=tk.HORIZONTAL)
        self._trvw = ttk.Treeview(
            self._frm_dnses,
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
        # Formating columns
        self._trvw.config(columns=(
            self._NAME_COL_IDX,
            self._RES_COL_IDX,
            self._DELAY_COL_IDX,))
        self._trvw.column('#0', width=0, stretch=tk.NO)  # Hidden column for tree structure
        self._trvw.column(
            self._NAME_COL_IDX,
            anchor=tk.W,
            width=100,
            stretch=False)
        self._trvw.column(
            self._RES_COL_IDX,
            anchor=tk.W,
            width=100,
            stretch=False)
        self._trvw.column(
            self._DELAY_COL_IDX,
            anchor=tk.W,
            width=100,
            stretch=False)
        # Create column headings
        self._trvw.heading('#0', text='', anchor=tk.W)  # Hidden heading for tree structure
        self._trvw.heading(self._NAME_COL_IDX, text=_('NAME'), anchor=tk.W)
        self._trvw.heading(self._RES_COL_IDX, text=_('RESPONSE'), anchor=tk.W)
        self._trvw.heading(
            self._DELAY_COL_IDX,
            text=_('LATENCY'),
            anchor=tk.W)
        #
        self._frm_btns = ttk.Frame(self._frm_container)
        self._frm_btns.grid(
            row=4,
            column=0,
            columnspan=2,
            padx=2,
            pady=2,
            sticky=tk.NSEW)
        #
        self._btn_startOk = ttk.Button(
            self._frm_btns,
            text=_('START'),
            width=10,
            command=self._start,
            default=tk.ACTIVE)
        self._btn_startOk.pack(side=tk.RIGHT, padx=5, pady=5)
        #
        self._btn_cancel = ttk.Button(
            self._frm_btns,
            text=_('CANCEL'),
            width=10,
            command=self._onCanceled)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def _start(self) -> None:
        self._btn_startOk.config(text=_('OK'))
        self._btn_startOk.config(state=tk.DISABLED)
    
    def showDialog(self) -> None:
        """Shows the dialog box and returns a `DnsServer` on completion
        or `None` on cancelation.
        """
        self.wm_deiconify()
        self.wait_window()
        return self._result
