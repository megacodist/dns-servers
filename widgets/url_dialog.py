#
# 
#

from queue import Empty, Queue
from threading import Event, Thread
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING, Iterator
from urllib.parse import ParseResult

from db import DnsServer
from utils.types import GifImage, TkImg

if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


def _codeToDescr(code: int) -> str:
    from http import HTTPStatus
    try:
        return HTTPStatus(code).phrase
    except ValueError:
        return _('Unknown Status Code')


class _Error:
    def __init__(self, msg: str) -> None:
        self.msg = msg


class _HttpRes:
    def __init__(
            self,
            code: int | None = None,
            latency: float = 0.0,
            description: str = '',
            ) -> None:
        self.code = code
        self.latency = latency
        self.description = description


class DnsTesterThrd(Thread):
    def __init__(
            self,
            url: str,
            net_int: str,
            inq: Queue[DnsServer],
            outq: Queue[str | _Error | _HttpRes],
            ) -> None:
        super().__init__(
            group=None,
            target=None,
            name='DNS tester thread',
            args=tuple(),
            kwargs=None,
            daemon=False)
        self._url = url
        self._netIntName = net_int
        """The name of the network interface which is using to test
        DNS servers.
        """
        self._inq = inq
        self._outq = outq
        self._cancel: Event | None = Event()
        self._TIMNT_NEW_DNS = 0.1
        """The timeout waiting for new DNS server."""
    
    def run(self) -> None:
        import socket
        from time import sleep, monotonic
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen
        from utils.funcs import setDns, readDnsInfo
        # Getting current DNS
        currDns = readDnsInfo(None, self._netIntName)
        # Starting main loop...
        while True:
            # Checking cancel is requested...
            if self._cancel.is_set(): # type: ignore
                self._cancel = None
                break
            # Getting next DNS test...
            try:
                dns = self._inq.get_nowait()
            except Empty:
                sleep(self._TIMNT_NEW_DNS)
                continue
            # Setting new DNS...
            self._outq.put(_('SETTING_DNS').format(
                self._netIntName, dns.name))
            setDns(None, self._netIntName, dns)
            readDns = readDnsInfo(None, self._netIntName)
            try:
                ipsEqual = dns.ipsToSet() == readDns.ipsToSet() # type: ignore
            except (TypeError, AttributeError):
                ipsEqual = False
            if not ipsEqual:
                self._outq.put(_Error(_('UNABLE_SET_DNS').format(dns.name)))
                continue
            # Checking accessibility of the URL through the newly-set DNS...
            self._outq.put(_('ACCESSING_URL'))
            response = _HttpRes()
            startTime = monotonic()
            try:
                httpReq = Request(self._url, method='HEAD')
                urlObj = urlopen(httpReq, timeout=5.0)
            except HTTPError as err:
                finishTime = monotonic()
                response.code = err.code
                response.description = _codeToDescr(err.code)
            except URLError as err:
                finishTime = monotonic()
                # Check if the reason for the URLError is a timeout
                if isinstance(err.reason, socket.timeout):
                    response.description = _('TIMEOUT')
                else:
                    response.description = str(err)
            else:
                finishTime = monotonic()
                response.code = urlObj.getcode()
                response.description = _codeToDescr(response.code)
                urlObj.close()
            response.latency = finishTime - startTime
            # Sending back the result...
            self._outq.put(response)
        # Rolling back the DNS...
        setDns(None, self._netIntName, currDns)
    
    def cancel(self) -> None:
        if self._cancel:
            self._cancel.set()
    
    def abortCanceling(self) -> None:
        """Aborts canceling. If canceling is in progress, it raises
        `TypeError`.
        """
        if self._cancel is None:
            raise TypeError()
        self._cancel.clear()


class UrlDialog(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            net_int: str,
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
        self._netIntName = net_int
        """The name of the network interface which is using to test
        DNS servers.
        """
        self._result = None
        self._mpNameDns = mp_name_dns
        self._mpNameRes = dict[str, _HttpRes]()
        self._mpNameIid = dict[str, str]()
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
        self._dnsTester: DnsTesterThrd | None = None
        self._outq = Queue[DnsServer]()
        self._inq = Queue[str | _Error | _HttpRes]()
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
        if self._dnsTester:
            self._dnsTester.cancel()
            self._dnsTester.join()
        self._result = None
        self.destroy()

    def _onCanceled(self) -> None:
        if self._dnsTester:
            self._dnsTester.cancel()
            self._dnsTester.join()
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
            text=_('LATENCY_HEAD'),
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
            self._mpNameIid[name] = iid
    
    def _validateUrl(self, url: str) -> bool:
        from utils.funcs import parseUrl
        url = url.strip()
        try:
            self._urlParts = parseUrl(url, scheme='https')
            self._lbl_url.config(foreground=self._validColor)
        except TypeError as err:
            self._urlParts = None
            self._lbl_url.config(foreground=self._invalidColor)
        return True
    
    def _start(self) -> None:
        from tkinter.messagebox import showerror
        from urllib.parse import urlunparse
        # Checking validity of URL...
        if not self._urlParts:
            showerror(message=_('INVALID_URL'))
            return
        #
        namesIter = iter(self._mpNameDns)
        try:
            dnsName = next(namesIter)
        except StopIteration:
            showerror(message=_('NO_DNS_TO_TEST'))
            return
        else:
            self._outq.put(self._mpNameDns[dnsName])
        #
        self._btn_startOk.config(text=_('OK'))
        self._btn_startOk.config(state=tk.DISABLED)
        self._svar_url.set(urlunparse(self._urlParts))
        self._entry_url.config(state=tk.DISABLED)
        #
        self._dnsTester = DnsTesterThrd(
            self._svar_url.get(),
            self._netIntName,
            self._outq,
            self._inq)
        self._dnsTester.start()
        self._afterId = self.after(
            self._TIMINT_AFTER,
            self._processDnses,
            dnsName,
            namesIter)
    
    def _processDnses(self, dns_name: str, names_iter: Iterator[str]) -> None:
        try:
            res = self._inq.get_nowait()
        except Empty:
            self._updateWaitGif(dns_name)
            nextDns = False
        else:
            if isinstance(res, str):
                self._showDnsMsg(dns_name, res)
                nextDns = False
            elif isinstance(res, _Error):
                self._showDnsErr(dns_name, res)
                nextDns = True
            elif isinstance(res, _HttpRes):
                self._mpNameRes[dns_name] = res
                self._showDnsRes(dns_name, res)
                nextDns = True
        if nextDns: # type: ignore
            try:
                dns_name = next(names_iter)
                self._outq.put(self._mpNameDns[dns_name])
            except StopIteration:
                # All testing finished...
                return
        # Scheduling next round...
        self._afterId = self.after(
            self._TIMINT_AFTER,
            self._processDnses,
            dns_name,
            names_iter)
    
    def _updateWaitGif(self, dns_name: str) -> None:
        self._trvw.see(self._mpNameIid[dns_name])
        self._trvw.item(
            self._mpNameIid[dns_name],
            image=self._GIF_DWAIT.nextFrame()) # type: ignore
    
    def _showDnsMsg(self, dns_name: str, msg: str) -> None:
        self._trvw.see(self._mpNameIid[dns_name])
        self._trvw.item(
            self._mpNameIid[dns_name],
            values=(dns_name, msg, ''))
    
    def _showDnsErr(self, dns_name: str, err: _Error) -> None:
        self._trvw.see(self._mpNameIid[dns_name])
        self._trvw.item(
            self._mpNameIid[dns_name],
            values=(dns_name, err.msg, ''))
        self._trvw.item(
            self._mpNameIid[dns_name],
            image=self._IMG_CROSS) # type: ignore
    
    def _showDnsRes(self, dns_name: str, res: _HttpRes) -> None:
        from utils.funcs import floatToEngineering as flToEngin
        self._trvw.see(self._mpNameIid[dns_name])
        self._trvw.item(
            self._mpNameIid[dns_name],
            values=(
                dns_name,
                self._getDescr(dns_name),
                flToEngin(self._mpNameRes[dns_name].latency, True) + 's'))
        if self._mpNameRes[dns_name].code and self._mpNameRes[
                dns_name].code // 100 == 2: # type: ignore
            self._trvw.item(self._mpNameIid[dns_name], image=self._IMG_TICK) # type: ignore
        else:
            self._trvw.item(self._mpNameIid[dns_name], image=self._IMG_CROSS) # type: ignore
    
    def _getDescr(self, dns_name: str) -> str:
        code = self._mpNameRes[dns_name].code
        descr = self._mpNameRes[dns_name].description
        if code is not None:
            return f'{code}: {descr}'
        else:
            return descr
    
    def showDialog(self) -> None:
        """Shows the dialog box and returns a `DnsServer` on completion
        or `None` on cancelation.
        """
        self.wm_deiconify()
        self.wait_window()
        return self._result
