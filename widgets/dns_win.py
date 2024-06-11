#
# 
#

from concurrent.futures import CancelledError, Future
from ipaddress import IPv4Address
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Callable, MutableSequence, TYPE_CHECKING

import PIL.Image
import PIL.ImageTk

from db import DnsServer, IDatabase

from .dns_view import Dnsview
from .interface_view import InterfaceView
from .message_view import MessageView, MessageType
from utils.async_ops import AsyncOpManager
from utils.settings import AppSettings
from utils.sorted_list import SortedList
from utils.types import GifImage, TkImg


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
        self._interfaces: MutableSequence[str]
        """A `MutableSequence` of all network interfaces."""
        self._dnses: MutableSequence[DnsServer]
        self._dnsNames = SortedList[str]()
        # Images...
        self._GIF_WAIT: GifImage
        self._HIMG_CLOSE: PIL.Image.Image
        self._HIMG_ADD: PIL.Image.Image
        self._HIMG_REMOVE: PIL.Image.Image
        self._HIMG_EDIT: PIL.Image.Image
        self._HIMG_APPLY: PIL.Image.Image
        self._IMG_CLOSE: TkImg
        self._IMG_ADD: TkImg
        self._IMG_REMOVE: TkImg
        self._IMG_EDIT: TkImg
        self._IMG_APPLY: TkImg
        # Loading resources...
        self._loadRes()
        # Initializing the GUI...
        self._initGui()
        self.update()
        self._pdwin.sashpos(0, self._settings.left_panel_width)
        # The rest of initializing...
        self._asyncMngr = AsyncOpManager(self, self._GIF_WAIT)
        # Bindings & events...
        self.protocol('WM_DELETE_WINDOW', self._onWinClosing)
        # Initializes views...
        self._initViews()
    
    def _loadRes(self) -> None:
        # Loading `wait.gif`...
        self._GIF_WAIT = GifImage(self._RES_DIR / 'wait.gif')
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
    
    def _initGui(self) -> None:
        #
        self._frm_container = tk.Frame(self)
        self._frm_container.pack(
            fill=tk.BOTH,
            expand=1,
            padx=7,
            pady=7)
        #
        self._pdwin = ttk.PanedWindow(
            master=self._frm_container,
            orient=tk.HORIZONTAL)
        self._pdwin.pack(
            fill=tk.BOTH,
            expand=1)
        #
        self._frm_leftPanel = tk.Frame(self._pdwin, relief=tk.SUNKEN)
        self._frm_leftPanel.columnconfigure(0, weight=1)
        self._frm_leftPanel.rowconfigure(0, weight=1)
        self._frm_leftPanel.rowconfigure(1, weight=1)
        self._frm_leftPanel.pack(fill=tk.BOTH, expand=1)
        self._pdwin.add(self._frm_leftPanel, weight=1)
        #
        self._frm_interDnses = tk.Frame(self._frm_leftPanel)
        self._frm_interDnses.columnconfigure(0, weight=1)
        self._frm_interDnses.columnconfigure(1, weight=1)
        self._frm_interDnses.rowconfigure(0, weight=1)
        self._frm_interDnses.grid(
            column=0,
            row=0,
            sticky=tk.NSEW,)
        #
        self._lfrm_interfaces = ttk.Labelframe(
            self._frm_interDnses,
            text=_('NET_INTERS'))
        self._lfrm_interfaces.grid(
            column=0,
            row=0,
            padx=3,
            pady=3,
            sticky=tk.NSEW,)
        #
        self._intervw = InterfaceView(
            self._lfrm_interfaces,
            self._onInterfaceChanged)
        self._intervw.pack(fill=tk.BOTH, expand=1)
        #
        self._lfrm_interDnses = ttk.Labelframe(self._frm_interDnses)
        self._lfrm_interDnses.columnconfigure(0, weight=1)
        self._lfrm_interDnses.grid(
            column=1,
            row=0,
            padx=3,
            pady=3,
            sticky=tk.NSEW,)
        #
        self._lbl_primary = ttk.Label(
            self._lfrm_interDnses,
            text=_('PRIMARY'))
        self._lbl_primary.grid(
            column=0,
            row=0,
            sticky=tk.W,)
        #
        self._entry_primary = ttk.Entry(self._lfrm_interDnses)
        self._entry_primary.grid(
            column=0,
            row=1,
            sticky=tk.NSEW,)
        #
        self._lbl_secondary = ttk.Label(
            self._lfrm_interDnses,
            text=_('SECONDARY'))
        self._lbl_secondary.grid(
            column=0,
            row=2,
            sticky=tk.W,)
        #
        self._entry_secondary = ttk.Entry(self._lfrm_interDnses)
        self._entry_secondary.grid(
            column=0,
            row=3,
            sticky=tk.NSEW,)
        #
        self._lfrm_dnses = ttk.Labelframe(
            self._frm_leftPanel,
            text=_('DNS_SERVERS'))
        self._lfrm_dnses.columnconfigure(0, weight=1)
        self._lfrm_dnses.rowconfigure(1, weight=1)
        self._lfrm_dnses.grid(
            column=0,
            row=1,
            padx=3,
            pady=3,
            sticky=tk.NSEW,)
        #
        self._frm_dnsButns = tk.Frame(self._lfrm_dnses)
        self._frm_dnsButns.grid(
            column=0,
            row=0,
            sticky=tk.NSEW,)
        #
        self._btn_addDns = ttk.Button(
            self._frm_dnsButns,
            command=self._addDns,
            image=self._IMG_ADD) # type: ignore
        self._btn_addDns.pack(
            side=tk.LEFT)
        #
        self._btn_deleteDns = ttk.Button(
            self._frm_dnsButns,
            command=self._deleteDns,
            image=self._IMG_REMOVE) # type: ignore
        self._btn_deleteDns.pack(
            side=tk.LEFT)
        #
        self._btn_editDns = ttk.Button(
            self._frm_dnsButns,
            command=self._editDns,
            image=self._IMG_EDIT) # type: ignore
        self._btn_editDns.pack(
            side=tk.LEFT)
        #
        self._btn_applyDns = ttk.Button(
            self._frm_dnsButns,
            image=self._IMG_APPLY) # type: ignore
        self._btn_applyDns.pack(
            side=tk.LEFT)
        #
        self._dnsvw = Dnsview(
            self._lfrm_dnses,
            self._editDns,
            name_col_width=self._settings.name_col_width,
            primary_col_width=self._settings.primary_col_width,
            secondary_col_width=self._settings.secondary_col_width)
        self._dnsvw.grid(
            column=0,
            row=1,
            sticky=tk.NSEW,)
        #
        self._msgvw = MessageView(self._pdwin, self._IMG_CLOSE)
        self._msgvw.pack(fill=tk.BOTH, expand=1)
        self._pdwin.add(self._msgvw, weight=1)
    
    def _onWinClosing(self) -> None:
        # Releasing images...
        self._GIF_WAIT.close()
        self._HIMG_CLOSE.close()
        self._HIMG_ADD.close()
        self._HIMG_REMOVE.close()
        self._HIMG_EDIT.close()
        self._HIMG_APPLY.close()
        #
        self._saveGeometry()
        self._settings.left_panel_width = self._pdwin.sashpos(0)
        colsWidth = self._dnsvw.getColsWidth()
        self._settings.name_col_width = colsWidth[0]
        self._settings.primary_col_width = colsWidth[1]
        self._settings.secondary_col_width = colsWidth[2]
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
        self._loadInterfaces()
        self._loadDnses()
    
    def _onInterfaceChanged(self, idx: int) -> None:
        from ntwrk import GetDnsServers
        self._lfrm_interDnses.config(text=self._interfaces[idx])
        print(GetDnsServers(self._interfaces[idx]))
    
    def _loadInterfaces(self) -> None:
        from utils.funcs import listInterfaces
        self._asyncMngr.InitiateOp(
            start_cb=listInterfaces,
            finish_cb=self._onInterfacesLoaded,
            widgets=(self._intervw,))
    
    def _onInterfacesLoaded(self, fut: Future[MutableSequence[str]]) -> None:
        from ntwrk import NetOpFailedError
        try:
            self._interfaces = fut.result()
            self._intervw.populate(self._interfaces)
        except CancelledError:
            self._msgvw.AddMessage(
                _('LOADING_INTERFACES_CANCELED'),
                type_=MessageType.INFO)
        except NetOpFailedError as err:
            self._msgvw.AddMessage(
                str(err),
                title=err.__class__.__qualname__,
                type_=MessageType.ERROR)
    
    def _loadDnses(self) -> None:
        from utils.funcs import listDnses
        self._asyncMngr.InitiateOp(
            start_cb=listDnses,
            start_args=(self._db,),
            finish_cb=self._onDnsesLoaded)

    def _onDnsesLoaded(self, fut: Future[MutableSequence[DnsServer]]) -> None:
        from utils.funcs import dnsToSetIps
        try:
            self._dnses = fut.result()
            self._dnsNames.items = [dns.name for dns in self._dnses]
            self._dnsvw.populate(self._dnses)
        except CancelledError:
            self._msgvw.AddMessage(
                _('LOADING_DNSES_CANCELED'),
                type_=MessageType.INFO)
    
    def _ipsExist(self, dns: DnsServer) -> int | None:
        """Checks if IPv4 objects of the DNS server exist, if so informs
        the user and returns its index otherwise returns `None`.
        """
        ipsSet = dns.ipsToSet()
        for idx, item in enumerate(self._dnses):
            if ipsSet == item.ipsToSet():
                return idx
        return None

    def _addDns(self) -> None:
        from .dns_dialog import DnsDialog
        from utils.funcs import dnsToSetIps
        dnsDialog = DnsDialog(self, self._dnsNames)
        dns = dnsDialog.showDialog()
        if dns is None:
            return
        # Checking existence of IPs...
        ipsIdx = self._ipsExist(dns)
        if isinstance(ipsIdx, int):
            self._msgvw.AddMessage(
                _('IPS_EXIST').format(self._dnses[ipsIdx].name),
                type_=MessageType.ERROR)
            return
        # Adding DNS server...
        self._dnses.append(dns)
        self._dnsNames.add(dns.name)
        self._db.insertDns(dns)
        self._dnsvw.appendDns(dns)
    
    def _deleteDns(self) -> None:
        from tkinter.messagebox import askyesno
        dnsIdx = self._dnsvw.getSetectedIdx()
        if dnsIdx is None:
            self._msgvw.AddMessage(
                _('SELECT_ITEM_DNS_VIEW'),
                type_=MessageType.WARNING)
            return
        dnsName = self._dnses[dnsIdx].name
        response = askyesno(message=_('CONFIRM_DEL_DNS').format(dnsName))
        if response is False:
            return
        del self._dnses[dnsIdx]
        del self._dnsNames[self._dnsNames.index(dnsName)[1]] # type: ignore
        self._db.deleteDns(dnsName)
        self._dnsvw.deleteIdx(dnsIdx)
    
    def _editDns(self) -> None:
        from .dns_dialog import DnsDialog
        from utils.funcs import dnsToSetIps
        idx = self._dnsvw.getSetectedIdx()
        if idx is None:
            self._msgvw.AddMessage(
                _('SELECT_ITEM_DNS_VIEW'),
                type_=MessageType.WARNING)
            return
        dnsName = self._dnses[idx].name
        slsIdx = self._dnsNames.index(dnsName)[1]
        if isinstance(slsIdx, slice):
            # Error: two or more DNS servers with the same name...
            logging.error('E-1', dnsName, stack_info=True)
            msg = _('DEL_DNS').format(dnsName)
            words = msg.split()
            words[0] = words[0].lower()
            msg = ' '.join(words)
            msg = _('ERROR').format(msg)
            self._msgvw.AddMessage(msg, 'E-1', MessageType.ERROR)
            return
        del self._dnsNames[slsIdx]
        dnsDialog = DnsDialog(self, self._dnsNames, self._dnses[idx])
        dns = dnsDialog.showDialog()
        logging.debug(dns)
        if (dns is None) or (dns == self._dnses[idx]):
            # No change, doing nothing...
            self._dnsNames.add(dnsName)
            return
        # Checking existence of IPs...
        ipsIdx = self._ipsExist(dns)
        if isinstance(ipsIdx, int):
            self._dnsNames.add(dnsName)
            self._msgvw.AddMessage(
                _('IPS_EXIST').format(self._dnses[ipsIdx].name),
                type_=MessageType.ERROR)
            return
        # Applying change...
        self._dnses[idx] = dns
        del self._dnsNames[slsIdx]
        self._dnsNames.add(dns.name)
        self._dnsvw.changeDns(idx, dns)
        self._db.updateDns(dnsName, dns)
