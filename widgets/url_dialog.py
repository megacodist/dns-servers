#
# 
#

from ipaddress import AddressValueError, IPv4Address
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING
from urllib.parse import ParseResult

from db import DnsServer
from utils.types import GifImage, TkImg

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
    def __init__(
            self,
            url: str,
            inq: Queue[DnsServer],
            outq: Queue[str | _HttpRes],
            ) -> None:
        super().__init__(
            group=None,
            target=None,
            name='DNS tester thread',
            args=tuple(),
            kwargs=None,
            daemon=False)
        self._url = url
        self._inq = inq
        self._outq = outq
    
    def run(self) -> None:
        return super().run()


class UrlDialog(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            mp_name_dns: dict[str, DnsServer],
            tick_img: TkImg,
            cross_img: TkImg,
            arrow_img: TkImg,
            wait_gif: GifImage,
            ) -> None:
        super().__init__(master)
        self.title(_('TEST_URL'))
        self.resizable(False, False)
        self.grab_set()
        #
        self._result = None
        self._mpNameDns = mp_name_dns
        self._mpNameRes = {key:_HttpRes() for key in self._mpNameDns}
        self._mpIidName = dict[str, str]()
        self._IMG_TICK = tick_img
        self._IMG_CROSS = cross_img
        self._IMG_ARROW = arrow_img
        self._GIF_DWAIT = wait_gif
        self._NAME_COL_IDX = 1
        self._RES_COL_IDX = 2
        self._DELAY_COL_IDX = 3
        self._TIMINT_AFTER = 40
        self._afterId: str | None = None
        self._validColor = 'green'
        self._invalidColor = '#ca482e'
        self._urlParts: ParseResult | None = None
        self._dnsTester: DnsTesterThrd
        self._outq = Queue[DnsServer]()
        self._inq = Queue[str | _HttpRes]()
        # Initializing the GUI...
        self._initGui()
        self._populateDnses()
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
        self._lbl_url = ttk.Label(self._frm_url, text=(_('URL') + ':'))
        self._lbl_url.config(foreground=self._invalidColor)
        self._lbl_url.pack(side=tk.LEFT, padx=2, pady=2)
        #
        self._svar_url = tk.StringVar(self)
        self._entry_url = ttk.Entry(
            self._frm_url,
            textvariable=self._svar_url,
            validate='key',
            validatecommand=(self.register(self._validateUrl), '%P'))
        self._entry_url.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        #
        self._frm_dnses = ttk.Frame(self._frm_container)
        self._frm_dnses.columnconfigure(0, weight=1)
        self._frm_dnses.rowconfigure(0, weight=1)
        self._frm_dnses.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
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
        self._trvw.column('#0', width=40, stretch=tk.NO)  # Hidden column for tree structure
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
        self._frm_btns.pack(fill=tk.X, expand=True, padx=2, pady=2)
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
    
    def _populateDnses(self) -> None:
        for name in self._mpNameDns:
            iid = self._trvw.insert(
                parent='',
                index=tk.END,
                image=self._IMG_ARROW, # type: ignore
                values=(self._mpNameDns[name].name, '', ''))
            self._mpIidName[iid] = name
    
    def _validateUrl(self, url: str) -> bool:
        from utils.funcs import parseUrl
        url = url.strip()
        try:
            self._urlParts = parseUrl(url, scheme='https')
            self._lbl_url.config(foreground=self._validColor)
        except TypeError as err:
            print(err)
            self._urlParts = None
            self._lbl_url.config(foreground=self._invalidColor)
        return True
    
    def _start(self) -> None:
        from tkinter.messagebox import showerror
        from urllib.parse import urlunparse
        # Checking validity of URL...
        if not self._urlParts:
            showerror()
            return
        #
        self._btn_startOk.config(text=_('OK'))
        self._btn_startOk.config(state=tk.DISABLED)
        self._svar_url.set(urlunparse(self._urlParts))
        self._entry_url.config(state=tk.DISABLED)
        #
        self._dnsTester = DnsTesterThrd(
            self._svar_url.get(),
            self._outq,
            self._inq)
        self._dnsTester.start()
        self._afterId = self.after(self._TIMINT_AFTER, self._processDnses, 0)
    
    def _processDnses(self, idx: int) -> None:
        try:
            res = self._inq.get_nowait()
        except Empty:
            self._mp
    
    def showDialog(self) -> None:
        """Shows the dialog box and returns a `DnsServer` on completion
        or `None` on cancelation.
        """
        self.wm_deiconify()
        self.wait_window()
        return self._result
