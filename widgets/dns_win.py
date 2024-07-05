#
# 
#

from concurrent.futures import CancelledError, Future
from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING, Literal

import PIL.Image
import PIL.ImageTk

from .dns_view import Dnsview
from .net_int_view import NetIntView
from .ips_view import IpsView
from .message_view import MessageView, MessageType
from db import DnsServer, IDatabase
from ntwrk import NetInt
from utils.async_ops import AsyncOpManager
from utils.settings import AppSettings
from utils.types import DnsInfo, GifImage, TkImg


if TYPE_CHECKING:
    _: Callable[[str], str]


class DnsWin(tk.Tk):
    def __init__(
            self,
            res_dir: Path,
            settings: AppSettings,
            db: IDatabase,) -> None:
        super().__init__(
            screenName=None,
            baseName=None,
            className='McDns',
            useTk=True,
            sync=False,
            use=None)
        self.title(_('APP_NAME'))
        self.geometry(f'{settings.win_width}x{settings.win_height}+'
            f'{settings.win_x}+{settings.win_y}')
        #
        self._RES_DIR = res_dir
        """The directory of the resources."""
        self._settings = settings
        """The application settings object."""
        self._db = db
        """The database object."""
        self._netInts: list[NetInt]
        """A list of all network interfaces."""
        self._mpNameDns: dict[str, DnsServer]
        self._mpIpDns: dict[frozenset[IPv4 | IPv6], DnsServer]
        # Images...
        self._GIF_WAIT: GifImage
        self._GIF_DWAIT: GifImage
        self._HIMG_CLOSE: PIL.Image.Image
        self._HIMG_ADD: PIL.Image.Image
        self._HIMG_REMOVE: PIL.Image.Image
        self._HIMG_EDIT: PIL.Image.Image
        self._HIMG_APPLY: PIL.Image.Image
        self._HIMG_GTICK: PIL.Image.Image
        self._HIMG_REDX: PIL.Image.Image
        self._HIMG_ARROW: PIL.Image.Image
        self._IMG_CLOSE: TkImg
        self._IMG_ADD: TkImg
        self._IMG_REMOVE: TkImg
        self._IMG_EDIT: TkImg
        self._IMG_APPLY: TkImg
        self._IMG_GTICK: TkImg
        self._IMG_REDX: TkImg
        self._IMG_ARROW: TkImg
        # Loading resources...
        self._loadRes()
        # Initializing the GUI...
        self._initGui()
        self.update()
        self._pwin_leftRight.sashpos(0, self._settings.net_int_ips_width)
        self.update_idletasks()
        self._pwin_netIntIps.sashpos(0, self._settings.net_int_height)
        self.update_idletasks()
        self._pwin_dnses.sashpos(0, self._settings.msgs_height)
        self.update_idletasks()
        self._pwin_urlsMsgs.sashpos(0, self._settings.urls_width)
        # The rest of initializing...
        self._asyncMngr = AsyncOpManager(self, self._GIF_WAIT)
        # Bindings & events...
        self.protocol('WM_DELETE_WINDOW', self._onWinClosing)
        # Initializes views...
        self.after(100, self._initViews)
    
    def _loadRes(self) -> None:
        # Loading `wait.gif`...
        self._GIF_WAIT = GifImage(self._RES_DIR / 'wait.gif')
        # Loading `dwait.gif`...
        self._GIF_DWAIT = GifImage(self._RES_DIR / 'dwait.gif', (16, 16,))
        # Loading `close.png`...
        self._HIMG_CLOSE = PIL.Image.open(self._RES_DIR / 'close.png')
        self._HIMG_CLOSE = self._HIMG_CLOSE.resize(size=(16, 16,))
        self._IMG_CLOSE = PIL.ImageTk.PhotoImage(image=self._HIMG_CLOSE)
        # Loading 'add.png...
        self._HIMG_ADD = PIL.Image.open(self._RES_DIR / 'add.png')
        self._HIMG_ADD = self._HIMG_ADD.resize(size=(16, 16,))
        self._IMG_ADD = PIL.ImageTk.PhotoImage(image=self._HIMG_ADD)
        # Loading 'remove.png...
        self._HIMG_REMOVE = PIL.Image.open(self._RES_DIR / 'remove.png')
        self._HIMG_REMOVE = self._HIMG_REMOVE.resize(size=(16, 16,))
        self._IMG_REMOVE = PIL.ImageTk.PhotoImage(image=self._HIMG_REMOVE)
        # Loading 'edit.png...
        self._HIMG_EDIT = PIL.Image.open(self._RES_DIR / 'edit.png')
        self._HIMG_EDIT = self._HIMG_EDIT.resize(size=(16, 16,))
        self._IMG_EDIT = PIL.ImageTk.PhotoImage(image=self._HIMG_EDIT)
        # Loading 'apply.png...
        self._HIMG_APPLY = PIL.Image.open(self._RES_DIR / 'apply.png')
        self._HIMG_APPLY = self._HIMG_APPLY.resize(size=(16, 16,))
        self._IMG_APPLY = PIL.ImageTk.PhotoImage(image=self._HIMG_APPLY)
        # Loading 'gtick.png...
        self._HIMG_GTICK = PIL.Image.open(self._RES_DIR / 'gtick.png')
        self._HIMG_GTICK = self._HIMG_GTICK.resize(size=(16, 16,))
        self._IMG_GTICK = PIL.ImageTk.PhotoImage(image=self._HIMG_GTICK)
        # Loading 'redx.png...
        self._HIMG_REDX = PIL.Image.open(self._RES_DIR / 'redx.png')
        self._HIMG_REDX = self._HIMG_REDX.resize(size=(16, 16,))
        self._IMG_REDX = PIL.ImageTk.PhotoImage(image=self._HIMG_REDX)
        # Loading 'arrow.png...
        self._HIMG_ARROW = PIL.Image.open(self._RES_DIR / 'arrow.png')
        self._HIMG_ARROW = self._HIMG_ARROW.resize(size=(16, 16,))
        self._IMG_ARROW = PIL.ImageTk.PhotoImage(image=self._HIMG_ARROW)

    def _initGui(self) -> None:
        #
        self._frm_container = tk.Frame(self)
        self._frm_container.pack(
            fill=tk.BOTH,
            expand=1,
            padx=7,
            pady=7)
        # Create the main PanedWindow (left and right)
        self._pwin_leftRight = ttk.PanedWindow(
            self._frm_container,
            orient=tk.HORIZONTAL)
        self._pwin_leftRight.pack(fill=tk.BOTH, expand=True)
        # Left pane content
        self._pwin_netIntIps = ttk.PanedWindow(
            self._pwin_leftRight,
            orient=tk.VERTICAL)
        self._pwin_netIntIps.pack(fill=tk.BOTH, expand=True)
        self._pwin_leftRight.add(self._pwin_netIntIps, weight=1)
        #
        self._lfrm_netInts = ttk.Labelframe(
            self._pwin_netIntIps,
            text=_('NET_INTS'))
        self._lfrm_netInts.pack(fill=tk.BOTH, expand=True)
        self._pwin_netIntIps.add(self._lfrm_netInts, weight=1)
        #
        self._netintvw = NetIntView(
            self._lfrm_netInts,
            self._readDnsInfo)
        self._netintvw.pack(fill=tk.BOTH, expand=1, padx=4, pady=4)
        #
        self._lfrm_ips = ttk.LabelFrame(self._pwin_netIntIps)
        self._lfrm_ips.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._pwin_netIntIps.add(self._lfrm_ips, weight=1)
        #
        self._ipsvw = IpsView(self._lfrm_ips)
        self._ipsvw.pack(fill=tk.BOTH, expand=True)
        # Right PanedWindow (upper and lower)
        self._pwin_dnses = ttk.PanedWindow(
            self._pwin_leftRight,
            orient=tk.VERTICAL)
        self._pwin_dnses.pack(fill=tk.BOTH, expand=True)
        self._pwin_leftRight.add(self._pwin_dnses, weight=2)
        # Upper PanedWindow (left and right)
        self._pwin_urlsMsgs = ttk.PanedWindow(
            self._pwin_dnses,
            orient=tk.HORIZONTAL)
        self._pwin_urlsMsgs.pack(fill=tk.BOTH, expand=True)
        self._pwin_dnses.add(self._pwin_urlsMsgs, weight=2)
        # Upper left pane content
        self._lfrm_urls = ttk.LabelFrame(self._pwin_urlsMsgs, text=_('URLS'))
        self._lfrm_urls.pack(fill=tk.BOTH, expand=True)
        self._pwin_urlsMsgs.add(self._lfrm_urls, weight=1)
        # Upper right pane content
        self._lfrm_msgs = ttk.LabelFrame(self._pwin_urlsMsgs, text=_('MSGS'))
        self._lfrm_msgs.pack(fill=tk.BOTH, expand=True)
        self._pwin_urlsMsgs.add(self._lfrm_msgs, weight=1)
        #
        self._msgvw = MessageView(self._lfrm_msgs, self._IMG_CLOSE)
        self._msgvw.pack(fill=tk.BOTH, expand=1, padx=4, pady=4)
        #
        self._lfrm_dnses = ttk.Labelframe(
            self._pwin_dnses,
            text=_('DNS_SERVERS'))
        self._lfrm_dnses.columnconfigure(0, weight=1)
        self._lfrm_dnses.rowconfigure(1, weight=1)
        self._lfrm_dnses.pack(fill=tk.BOTH, expand=True)
        self._pwin_dnses.add(self._lfrm_dnses, weight=1)
        #
        self._frm_dnsButns = tk.Frame(self._lfrm_dnses)
        self._frm_dnsButns.grid(
            column=0,
            row=0,
            padx=4,
            pady=4,
            sticky=tk.NSEW,)
        #
        self._btn_addDns = ttk.Button(
            self._frm_dnsButns,
            command=self._addDns,
            image=self._IMG_ADD) # type: ignore
        self._btn_addDns.pack(side=tk.LEFT)
        #
        self._btn_deleteDns = ttk.Button(
            self._frm_dnsButns,
            command=self._deleteDns,
            image=self._IMG_REMOVE) # type: ignore
        self._btn_deleteDns.pack(side=tk.LEFT)
        #
        self._btn_editDns = ttk.Button(
            self._frm_dnsButns,
            command=self._editDns,
            image=self._IMG_EDIT) # type: ignore
        self._btn_editDns.pack(side=tk.LEFT)
        #
        self._btn_applyDns = ttk.Button(
            self._frm_dnsButns,
            command=self._applyDns,
            image=self._IMG_APPLY) # type: ignore
        self._btn_applyDns.pack(side=tk.LEFT)
        #
        self._dnsvw = Dnsview(
            self._lfrm_dnses,
            self._editDns,
            name_col_width=self._settings.name_col_width,
            prim_4_col_width=self._settings.prim_4_col_width,
            secon_4_col_width=self._settings.secon_4_col_width,
            prim_6_col_width=self._settings.prim_6_col_width,
            secon_6_col_width=self._settings.secon_6_col_width,)
        self._dnsvw.grid(
            column=0,
            row=1,
            sticky=tk.NSEW,)
        # Creating menu bar...
        self._menubar = tk.Menu(
            master=self)
        self.config(menu=self._menubar)
        # Creating `App` menu...
        self._menu_app = tk.Menu(
            master=self._menubar,
            tearoff=0)
        self._menubar.add_cascade(
            label=_('APP'),
            menu=self._menu_app)
        self._menu_app.add_cascade(
            label=_('QUIT'),
            command=self._onWinClosing)
        # Creating `Commands` menu...
        self._menu_cmds = tk.Menu(
            master=self._menubar,
            tearoff=0)
        self._menubar.add_cascade(
            label=_('CMDS'),
            menu=self._menu_cmds)
        self._menu_cmds.add_command(
            label=_('CLEAR_MSGS'),
            command=self._msgvw.Clear)
        self._menu_cmds.add_cascade(
            label=_('READ_INTERFACES'),
            command=self._readNetInts)
        self._menu_cmds.add_cascade(
            label=_('READ_DNSES'),
            command=self._readDnses)
        self._menu_cmds.add_cascade(
            label=_('TEST_URL'),
            command=self._testUrl)
    
    def _onWinClosing(self) -> None:
        # Releasing images...
        self._GIF_WAIT.close()
        self._GIF_DWAIT.close()
        self._HIMG_CLOSE.close()
        self._HIMG_ADD.close()
        self._HIMG_REMOVE.close()
        self._HIMG_EDIT.close()
        self._HIMG_APPLY.close()
        self._HIMG_GTICK.close()
        self._HIMG_REDX.close()
        self._HIMG_ARROW.close()
        #
        self._saveGeometry()
        self._settings.net_int_ips_width = self._pwin_leftRight.sashpos(0)
        self._settings.net_int_height = self._pwin_netIntIps.sashpos(0)
        self._settings.msgs_height = self._pwin_dnses.sashpos(0)
        self._settings.urls_width = self._pwin_urlsMsgs.sashpos(0)
        colsWidth = self._dnsvw.getColsWidth()
        self._settings.name_col_width = colsWidth[0]
        self._settings.prim_4_col_width = colsWidth[1]
        self._settings.secon_4_col_width = colsWidth[2]
        self._settings.prim_6_col_width = colsWidth[3]
        self._settings.secon_6_col_width = colsWidth[4]
        # Cleaning up...
        self._asyncMngr.close()
        # Destroying the window...
        self.destroy()
    
    def _saveGeometry(self) -> None:
        """Saves the geometry of the window to the app settings object."""
        import re
        w_h_x_y = self.winfo_geometry()
        GEOMETRY_REGEX = r"""
            (?P<width>\d+)    # The width of the window
            x(?P<height>\d+)  # The height of the window
            \+(?P<x>\d+)      # The x-coordinate of the window
            \+(?P<y>\d+)      # The y-coordinate of the window"""
        match = re.search(
            GEOMETRY_REGEX,
            w_h_x_y,
            re.VERBOSE)
        if match:
            self._settings.win_width = int(match.group('width'))
            self._settings.win_height = int(match.group('height'))
            self._settings.win_x = int(match.group('x'))
            self._settings.win_y = int(match.group('y'))
        else:
            logging.error(
                'Cannot get the geometry of the window.', stack_info=True)
    
    def _initViews(self) -> None:
        """Initializes the interface view and the """
        self._readNetInts()
        self._readDnses()
    
    def _readDnsInfo(self, idx: int | None) -> None:
        if idx is None:
            return
        self._lfrm_ips.config(text=self._netInts[idx].NetConnectionID)
        self._ipsvw.populate(self._netInts[idx], self._mpNameDns.values())

    
    def _onDnsInfoRead(self, fut: Future[DnsInfo | Literal['DHCP']]) -> None:
        from utils.funcs import mergeMsgs
        try:
            res = fut.result()
            self._populateDnsInfoPanel(res)
        except CancelledError:
            self._msgvw.AddMessage(
                _('X_CANCELED').format(_('READING_DNS_INFO')),
                type_=MessageType.INFO,)
    
    def _readNetInts(self) -> None:
        """Reads network interfaces."""
        from utils.funcs import readNetInts
        self._asyncMngr.InitiateOp(
            start_cb=readNetInts,
            finish_cb=self._onNetIntsRead,
            widgets=(self._netintvw,))
    
    def _onNetIntsRead(self, fut: Future[list[NetInt]]) -> None:
        try:
            self._netInts = fut.result()
            self._netintvw.populate(self._netInts)
        except CancelledError:
            self._msgvw.AddMessage(
                _('X_CANCELED').format(_('READING_INTERFACES')),
                type_=MessageType.INFO)
    
    def _readDnses(self) -> None:
        from utils.funcs import listDnses
        self._asyncMngr.InitiateOp(
            start_cb=listDnses,
            start_args=(self._db,),
            finish_cb=self._onDnsesRead)

    def _onDnsesRead(
            self,
            fut: Future[tuple[dict[str, DnsServer], dict[
                frozenset[IPv4 | IPv6], DnsServer]]],
            ) -> None:
        try:
            self._mpNameDns, self._mpIpDns = fut.result()
            self._dnsvw.populate(self._mpNameDns.values())
        except CancelledError:
            self._msgvw.AddMessage(
                _('X_CANCELED').format(_('READING_DNSES')),
                type_=MessageType.INFO)
    
    def _getNetInt(self) -> str | None:
        """Gets the selected network interface name. If nothing is
        selected, it informs the user and returns `None`.
        """
        interIdx = self._netintvw.getSelectedIdx()
        if interIdx is None:
            self._msgvw.AddMessage(
                _('SELECT_ITEM_INTER_VIEW'),
                type_=MessageType.WARNING)
            return
        return self._netInts[interIdx]['Name'] # type: ignore
    
    def _applyDns(self) -> None:
        # Getting interface...
        interName = self._getNetInt()
        if interName is None:
            return
        # Getting DNS...
        dnsName = self._dnsvw.getSetectedName()
        if dnsName is None:
            self._msgvw.AddMessage(
                _('SELECT_ITEM_DNS_VIEW'),
                type_=MessageType.WARNING)
            return
        #
        from utils.funcs import setDns
        self._asyncMngr.InitiateOp(
            start_cb=setDns,
            start_args=(interName, self._mpNameDns[dnsName]),
            finish_cb=self._onDnsApplied,
            widgets=(self._lfrm_dnsInfo,))

    def _onDnsApplied(self, fut: Future[None]) -> None:
        try:
            fut.result()
        except CancelledError:
            self._msgvw.AddMessage(
                _('X_CANCELED').format(_('SETTING_DNS')),
                type_=MessageType.INFO)
        else:
            self._readDnsInfo(self._netintvw.getSelectedIdx())

    def _addDns(self) -> None:
        from .dns_dialog import DnsDialog
        dnsDialog = DnsDialog(self, self._mpNameDns)
        dns = dnsDialog.showDialog()
        if dns is None:
            return
        # Checking that IPs already exist...
        ipsSet = dns.ipsToSet()
        if ipsSet in self._mpIpDns:
            self._msgvw.AddMessage(
                _('IPS_EXIST').format(self._mpIpDns[ipsSet].name),
                type_=MessageType.ERROR)
            return
        # Adding DNS server...
        self._mpIpDns[ipsSet] = dns
        self._mpNameDns[dns.name] = dns
        self._db.insertDns(dns)
        self._dnsvw.appendDns(dns)
    
    def _deleteDns(self) -> None:
        from tkinter.messagebox import askyesno
        dnsName = self._dnsvw.getSetectedName()
        if dnsName is None:
            self._msgvw.AddMessage(
                _('SELECT_ITEM_DNS_VIEW'),
                type_=MessageType.WARNING)
            return
        response = askyesno(message=_('CONFIRM_DEL_DNS').format(dnsName))
        if response is False:
            return
        ipsSet = self._mpNameDns[dnsName].ipsToSet()
        del self._mpNameDns[dnsName]
        del self._mpIpDns[ipsSet]
        self._db.deleteDns(dnsName)
        self._dnsvw.deleteName(dnsName)
    
    def _editDns(self) -> None:
        from .dns_dialog import DnsDialog
        from utils.funcs import mergeMsgs
        dnsName = self._dnsvw.getSetectedName()
        if dnsName is None:
            self._msgvw.AddMessage(
                _('SELECT_ITEM_DNS_VIEW'),
                type_=MessageType.WARNING)
            return
        dnsIps = self._mpNameDns[dnsName].ipsToSet()
        cpyNameDns = self._mpNameDns.copy()
        del cpyNameDns[dnsName]
        dnsDialog = DnsDialog(self, cpyNameDns, self._mpNameDns[dnsName])
        newDns = dnsDialog.showDialog()
        if (newDns is None) or (newDns == self._mpNameDns[dnsName]):
            # No change, doing nothing...
            return
        # Checking existence of IPs...
        if newDns.ipsToSet() in cpyNameDns:
            self._msgvw.AddMessage(
                _('IPS_EXIST').format(self._mpIpDns[newDns.ipsToSet()].name),
                type_=MessageType.ERROR)
            return
        # Applying change...
        self._mpNameDns[newDns.name] = newDns
        if newDns.name != dnsName:
            del self._mpNameDns[dnsName]
        self._mpIpDns[newDns.ipsToSet()] = newDns
        if newDns.ipsToSet() != dnsIps:
            del self._mpIpDns[dnsIps]
        self._dnsvw.changeDns(dnsName, newDns)
        self._db.updateDns(dnsName, newDns)
    
    def _populateDnsInfoPanel(self, dns: DnsInfo | Literal['DHCP']) -> None:
        from utils.funcs import ipToStr
        logging.debug(dns)
        if dns is 'DHCP':
            self._entry_primary.insert(0, '')
            self._entry_secondary.insert(0, '')
            self._msg_dnsName.config(width=self._msg_dnsName.winfo_width())
            self._msg_dnsName.config(text='DHCP')
        elif isinstance(dns, DnsInfo):
            self._entry_primary.insert(0, ipToStr(dns.primary))
            self._entry_secondary.insert(0, ipToStr(dns.secondary))
            try:
                name = self._mpIpDns[dns.ipsToSet()].name
            except KeyError:
                name = ''
            self._msg_dnsName.config(width=self._msg_dnsName.winfo_width())
            self._msg_dnsName.config(text=name)
        else:
            logging.error('E3', dns)
    
    def _testUrl(self) -> None:
        # Reading network interface name...
        netIntName = self._getNetInt()
        if netIntName is None:
            return
        #
        from widgets.url_dialog import UrlDialog
        dnsDialog = UrlDialog(
            self,
            netIntName,
            self._mpNameDns,
            self._IMG_GTICK,
            self._IMG_REDX,
            self._IMG_ARROW,
            self._GIF_DWAIT)
        dns = dnsDialog.showDialog()
        if dns is None:
            return
