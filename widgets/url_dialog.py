#
# 
#

from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
from queue import Empty, Queue
from threading import Event, Thread
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING, Iterable, Iterator
from urllib.parse import ParseResult

from db import DnsServer
from ntwrk import NetConfig, NetConfigCode
from utils.types import GifImage, TkImg

type _Iid = str

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
            config: NetConfig,
            ips_q: Queue[Iterable[IPv4 | IPv6]],
            res_q: Queue[str | _Error | _HttpRes],
            ) -> None:
        super().__init__(
            group=None,
            target=None,
            name='DNS tester thread',
            args=tuple(),
            kwargs=None,
            daemon=False)
        self._url = url
        self._config = config
        """The network adapter configuration which is using to test DNS
        servers.
        """
        self._qIps = ips_q
        self._qRes = res_q
        self._cancel: Event | None = Event()
        self._TIMNT_WAIT = 0.1
        """The timeout waiting for new DNS server."""
    
    def run(self) -> None:
        import socket
        from time import sleep, monotonic
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen
        # Getting current DNS
        origIps = self._config.DNSServerSearchOrder
        # Starting main loop...
        while True:
            # Checking cancel is requested...
            if self._cancel.is_set(): # type: ignore
                self._cancel = None
                break
            # Getting next DNS test...
            try:
                ips = self._qIps.get_nowait()
            except Empty:
                sleep(self._TIMNT_WAIT)
                continue
            # Setting new DNS...
            self._qRes.put(_('SETTING_DNS'))
            code = self._config.setDnsSearchOrder(ips)
            if code != NetConfigCode.SUCCESSFUL:
                if code.__doc__ is None:
                    msg = _('UNABLE_CHANGE_IPS').format(code.name)
                else:
                    msg = _('UNABLE_CHANGE_IPS').format(code.__doc__)
                self._qRes.put(_Error(msg))
                continue
            # Checking accessibility of the URL through the newly-set DNS...
            self._qRes.put(_('ACCESSING_URL'))
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
            self._qRes.put(response)
        # Rolling back the DNS...
        if origIps is not None:
            self._config.setDnsSearchOrder(origIps)
    
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
            config: NetConfig,
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
        self._config = config
        """The network adapter configuration which is using to test DNS
        servers.
        """
        self._result = None
        self._mpNameDns = mp_name_dns
        self._mpNameRes = dict[_Iid, _HttpRes]()
        self._mpReqIssued = dict[_Iid, _Iid]()
        """The mapping between requested iis and issued iids:

        `redIid -> issuedIid`
        """
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
        self._SEP = '#*#'
        self._urlParts: ParseResult | None = None
        self._dnsTester: DnsTesterThrd | None = None
        self._qIps = Queue[Iterable[IPv4 | IPv6]]()
        self._qRes = Queue[str | _Error | _HttpRes]()
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
        self._trvw.column('#0', width=60, stretch=tk.NO)  # Hidden column for tree structure
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
    
    def _getIssuedIid(self, req_iid: _Iid) -> _Iid:
        """Gets the issued iid of the requested iid."""
        if req_iid is self._mpReqIssued:
            return self._mpReqIssued[req_iid]
        return req_iid
    
    def _iterChildIids(self) -> Iterator[_Iid]:
        """Returns an iterator to iterate over all Ips in all DNSes."""
        for parentIid in self._trvw.get_children(''):
            for childIid in self._trvw.get_children(parentIid):
                yield childIid
    
    def _populateDnses(self) -> None:
        reqIid = 'DHCP'
        issuedIid = self._trvw.insert(
            parent='',
            index=tk.END,
            iid=reqIid,
            values=(_('DHCP'), '', '',),)
        if reqIid != issuedIid:
            self._mpReqIssued[reqIid] = issuedIid
        for name, dns in self._mpNameDns.items():
            reqIid = name
            issuedIid = self._trvw.insert(
                parent='',
                index=tk.END,
                iid=reqIid,
                open=True,
                values=(name,),)
            if reqIid != issuedIid:
                self._mpReqIssued[reqIid] = issuedIid
            parentIid = issuedIid
            for idx, ip in enumerate(dns.toIpTuple()):
                reqIid = f'{name}{self._SEP}{idx}'
                issuedIid = self._trvw.insert(
                    parent=parentIid,
                    index=tk.END,
                    iid=reqIid,
                    values=(str(ip), '', '',),)
                if reqIid != issuedIid:
                    self._mpReqIssued[reqIid] = issuedIid
    
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
        self._btn_startOk.config(text=_('OK'))
        self._btn_startOk.config(state=tk.DISABLED)
        self._svar_url.set(urlunparse(self._urlParts))
        self._entry_url.config(state=tk.DISABLED)
        #
        ipsIter = self._iterChildIids()
        iid = self._getIssuedIid('DHCP')
        self._qIps.put([])
        #
        self._dnsTester = DnsTesterThrd(
            self._svar_url.get(),
            self._config,
            self._qIps,
            self._qRes)
        self._dnsTester.start()
        self._afterId = self.after(
            self._TIMINT_AFTER,
            self._pollResult,
            iid,
            ipsIter)
    
    def _pollResult(
            self,
            curr_iid: _Iid,
            iter_: Iterator[_Iid],
            ) -> None:
        # Polling for the result...
        try:
            res = self._qRes.get_nowait()
        except Empty:
            self._updateWaitGif(curr_iid)
            nextIp = False
        else:
            if isinstance(res, str):
                self._showMsg(curr_iid, res)
                self._updateWaitGif(curr_iid)
                nextIp = False
            elif isinstance(res, _Error):
                self._showMsg(curr_iid, res.msg)
                self._showErrImg(curr_iid)
                nextIp = True
            elif isinstance(res, _HttpRes):
                self._mpNameRes[curr_iid] = res
                self._showRes(curr_iid, res)
                self._showResImg(curr_iid)
                nextIp = True
        # Scheduling next action...
        if nextIp: # type: ignore
            self._afterId = self.after(
                self._TIMINT_AFTER,
                self._testNextIp,
                iter_,)
        else:
            self._afterId = self.after(
                self._TIMINT_AFTER,
                self._pollResult,
                curr_iid,
                iter_,)
    
    def _testNextIp(self, child_iter: Iterator[_Iid]) -> None:
        try:
            curr_iid = next(child_iter)
        except StopIteration:
            # Process finished...
            self._btn_startOk.config(state=tk.NORMAL)
        else:
            ip = self._getIpByIid(curr_iid)
            self._qIps.put([ip,])
            self._afterId = self.after(
                self._TIMINT_AFTER,
                self._pollResult,
                curr_iid,
                child_iter,)
    
    def _updateWaitGif(self, iid: _Iid) -> None:
        self._trvw.see(iid)
        self._trvw.item(
            iid,
            image=self._GIF_DWAIT.nextFrame()) # type: ignore
    
    def _showErrImg(self, iid: _Iid) -> None:
        self._trvw.item(
            iid,
            image=self._IMG_CROSS) # type: ignore

    def _showOkImg(self, iid: _Iid) -> None:
        self._trvw.item(
            iid,
            image=self._IMG_TICK) # type: ignore
    
    def _showMsg(self, iid: _Iid, msg: str) -> None:
        values = self._trvw.item(iid, option='values')
        values = list(values)
        values[1] = msg
        self._trvw.see(iid)
        self._trvw.item(
            iid,
            values=tuple(values),)
    
    def _showRes(self, iid: _Iid, res: _HttpRes) -> None:
        from utils.funcs import floatToEngineering as flToEngin
        values = self._trvw.item(iid, option='values')
        self._trvw.see(iid)
        self._trvw.item(
            iid,
            values=(
                values[0],
                self._getDescr(iid),
                flToEngin(self._mpNameRes[iid].latency, True) + 's'))
    
    def _showResImg(self, iid: _Iid) -> None:
        if self._mpNameRes[iid].code and self._mpNameRes[
                iid].code // 100 == 2: # type: ignore
            self._showOkImg(iid)
        else:
            self._showErrImg(iid)
    
    def _getIpByIid(self, iid: _Iid) -> IPv4 | IPv6:
        iid_ = self._getIssuedIid(iid)
        dnsName, ipIdx = iid_.split(self._SEP)
        ipIdx = int(ipIdx)
        return self._mpNameDns[dnsName].toIpTuple()[ipIdx]
    
    def _getDescr(self, iid: _Iid) -> str:
        code = self._mpNameRes[iid].code
        descr = self._mpNameRes[iid].description
        if code is not None:
            return f'{code}: {descr}'
        else:
            return descr
    
    def showDialog(self) -> None:
        """Shows the dialog box and returns a `DnsServer` on completion
        or `None` on cancelation.
        """
        self.grab_set()
        self.focus_set()
        self.wm_deiconify()
        self.wait_window()
        return self._result
