#
# 
#

from concurrent.futures import CancelledError, Future
from ipaddress import IPv4Address as IPv4, IPv6Address as IPv6
import logging
from pathlib import Path
from queue import Queue
import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING

import PIL.Image
import PIL.ImageTk

from .dns_view import Dnsview
from .net_adap_view import NetAdapsView
from .ips_view import IpsView
from .message_view import MessageView, MessageType
from db import DnsServer, IDatabase
from ntwrk import ACIdx, AdapCfgBag, NetAdap, NetConfig, NetConfigCode
from utils.async_ops import AsyncOpManager
from utils.keyboard import KeyCodes, Modifiers
from utils.net_int_monitor import NetItemMonitor
from utils.settings import AppSettings
from utils.types import GifImage, TkImg
from widgets.net_int_dialog import NetItemInfoWin


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
        self._acbag: AdapCfgBag
        """An instance of `AdapCfgBag`, a bag of adapter-config objects."""
        self._qAdapChange = Queue[NetAdap]()
        self._qAdapCreation = Queue[NetAdap]()
        self._qAdapDeletion = Queue[NetAdap]()
        self._qConfigChange = Queue[NetConfig]()
        self._qConfigCreation = Queue[NetConfig]()
        self._qConfigDeletion = Queue[NetConfig]()
        self._netItemThrd: NetItemMonitor
        """The thread looking for changes in network interfaces."""
        self._infoWins = dict[ACIdx, NetItemInfoWin]()
        self._mpNameDns: dict[str, DnsServer]
        self._mpIpDns: dict[IPv4 | IPv6, DnsServer]
        # Images...
        self._GIF_WAIT: GifImage
        self._GIF_DWAIT: GifImage
        self._HIMG_CLOSE: PIL.Image.Image
        self._HIMG_ADD: PIL.Image.Image
        self._HIMG_REMOVE: PIL.Image.Image
        self._HIMG_EDIT: PIL.Image.Image
        self._HIMG_GTICK: PIL.Image.Image
        self._HIMG_REDX: PIL.Image.Image
        self._HIMG_ARROW: PIL.Image.Image
        self._HIMG_GINET: PIL.Image.Image
        self._HIMG_RINET: PIL.Image.Image
        self._HIMG_GNTWRK: PIL.Image.Image
        self._HIMG_RNTWRK: PIL.Image.Image
        self._IMG_CLOSE: TkImg
        self._IMG_ADD: TkImg
        self._IMG_REMOVE: TkImg
        self._IMG_EDIT: TkImg
        self._IMG_GTICK: TkImg
        self._IMG_REDX: TkImg
        self._IMG_ARROW: TkImg
        self._IMG_GINET: TkImg
        self._IMG_RINET: TkImg
        self._IMG_GNTWRK: TkImg
        self._IMG_RNTWRK: TkImg
        # Loading resources...
        print(_('LOADING_RES'))
        self._loadRes()
        # Initializing the GUI...
        print(_('CREATING_WIN'))
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
        self.bind('<Key>', self._onKeyPressed)
        self.protocol('WM_DELETE_WINDOW', self._onWinClosing)
        self.bind('<<NetAdapChanged>>', self._onNetAdapChanged)
        self.bind('<<NetAdapCreated>>', self._onNetAdapCreated)
        self.bind('<<NetAdapDeleted>>', self._onNetAdapDeleted)
        self.bind('<<NetConfigChanged>>', self._onNetConfigChanged)
        self.bind('<<NetConfigCreated>>', self._onNetConfigCreated)
        self.bind('<<NetConfigDeleted>>', self._onNetConfigDeleted)
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
        # Loading 'ginet.png...
        self._HIMG_GINET = PIL.Image.open(self._RES_DIR / 'ginet.png')
        self._HIMG_GINET = self._HIMG_GINET.resize(size=(16, 16,))
        self._IMG_GINET = PIL.ImageTk.PhotoImage(image=self._HIMG_GINET)
        # Loading 'rinet.png...
        self._HIMG_RINET = PIL.Image.open(self._RES_DIR / 'rinet.png')
        self._HIMG_RINET = self._HIMG_RINET.resize(size=(16, 16,))
        self._IMG_RINET = PIL.ImageTk.PhotoImage(image=self._HIMG_RINET)
        # Loading 'gconn.png...
        self._HIMG_GNTWRK = PIL.Image.open(self._RES_DIR / 'gconn.png')
        self._HIMG_GNTWRK = self._HIMG_GNTWRK.resize(size=(16, 16,))
        self._IMG_GNTWRK = PIL.ImageTk.PhotoImage(image=self._HIMG_GNTWRK)
        # Loading 'rconn.png...
        self._HIMG_RNTWRK = PIL.Image.open(self._RES_DIR / 'rconn.png')
        self._HIMG_RNTWRK = self._HIMG_RNTWRK.resize(size=(16, 16,))
        self._IMG_RNTWRK = PIL.ImageTk.PhotoImage(image=self._HIMG_RNTWRK)

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
        self._lfrm_netAdaps = ttk.Labelframe(
            self._pwin_netIntIps,
            text=_('NET_ADAPS'))
        self._lfrm_netAdaps.pack(fill=tk.BOTH, expand=True)
        self._pwin_netIntIps.add(self._lfrm_netAdaps, weight=1)
        #
        self._adapsvw = NetAdapsView(
            self._lfrm_netAdaps,
            self._readDnsInfo,
            self._showInfoWin,
            gntwrk_img=self._IMG_GNTWRK,
            rntwrk_img=self._IMG_RNTWRK,
            ginet_img=self._IMG_GINET,
            rinet_img=self._IMG_RINET,)
        self._adapsvw.pack(fill=tk.BOTH, expand=1, padx=4, pady=4)
        #
        self._lfrm_ips = ttk.LabelFrame(self._pwin_netIntIps)
        self._lfrm_ips.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._pwin_netIntIps.add(self._lfrm_ips, weight=1)
        #
        self._frm_ipsTlbr = ttk.Frame(self._lfrm_ips)
        self._frm_ipsTlbr.pack(fill=tk.X, expand=True)
        #
        self._btn_addIps = ttk.Button(
            self._frm_ipsTlbr,
            image=self._IMG_ADD) # type: ignore
        self._btn_addIps.pack(side=tk.LEFT)
        #
        self._btn_deletIps = ttk.Button(
            self._frm_ipsTlbr,
            image=self._IMG_REMOVE) # type: ignore
        self._btn_deletIps.pack(side=tk.LEFT)
        #
        self._btn_setIps = ttk.Button(
            self._frm_ipsTlbr,
            command=self._setIps,
            image=self._IMG_ARROW) # type: ignore
        self._btn_setIps.pack(side=tk.LEFT)
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
        self._frm_dnsTlbr = tk.Frame(self._lfrm_dnses)
        self._frm_dnsTlbr.grid(
            column=0,
            row=0,
            padx=4,
            pady=4,
            sticky=tk.NSEW,)
        #
        self._btn_addDns = ttk.Button(
            self._frm_dnsTlbr,
            command=self._addDns,
            image=self._IMG_ADD) # type: ignore
        self._btn_addDns.pack(side=tk.LEFT)
        #
        self._btn_deleteDns = ttk.Button(
            self._frm_dnsTlbr,
            command=self._deleteDns,
            image=self._IMG_REMOVE) # type: ignore
        self._btn_deleteDns.pack(side=tk.LEFT)
        #
        self._btn_editDns = ttk.Button(
            self._frm_dnsTlbr,
            command=self._editDns,
            image=self._IMG_EDIT) # type: ignore
        self._btn_editDns.pack(side=tk.LEFT)
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
        # Creating `Adapters` menu...
        self._menu_netAdaps = tk.Menu(
            master=self._menubar,
            tearoff=0)
        self._menubar.add_cascade(
            label=_('NET_ADAPS'),
            menu=self._menu_netAdaps)
        self._menu_netAdaps.add_cascade(
            label=_('READ_INTERFACES'),
            command=self._readNetAdaps)
        self._menu_netAdaps.add_cascade(
            label=_('SHOW_NET_INT_INFO'),
            command=self._showInfoWin)
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
        self._HIMG_GTICK.close()
        self._HIMG_REDX.close()
        self._HIMG_ARROW.close()
        self._HIMG_GINET.close()
        self._HIMG_RINET.close()
        self._HIMG_GNTWRK.close()
        self._HIMG_RNTWRK.close()
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
        try:
            self._netItemThrd.cancel()
        except AttributeError:
            pass
        else:
            self._netItemThrd.join()
        # Closing open NetItemInfoWin windows...
        lsInfoWins = list(self._infoWins.values())
        for netWin in lsInfoWins[:-1]:
            netWin.destroy()
        lsInfoWins[-1].closeWin()
        self._grabInoWinSettings(lsInfoWins[-1])
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
    
    def _onKeyPressed(self, event: tk.Event) -> None:
        if isinstance(event.state, str):
            logging.error('invalid state\n%s: str', event.state)
            return
        if (event.state & Modifiers.CONTROL) == Modifiers.CONTROL:
            # Checking Ctrl+O...
            if event.keycode == KeyCodes.O:
                for idx, adap in self._acbag.iterAdaps():
                    if adap.NetConnectionID == 'Ethernet':
                        pass
    
    def _onNetAdapChanged(self, _: tk.Event) -> None:
        newAdap = self._qAdapChange.get()
        try:
            adapIdx = self._acbag.indexAdap(newAdap)
        except IndexError:
            logging.info(
                '%s was changed while has not loaded into the bag.',
                newAdap,)
            return
        except ValueError:
            logging.error(
                '%s was changed while has contradictory peer in the bag.',
                newAdap,)
            return
        curAdap: NetAdap = self._acbag[adapIdx] # type: ignore
        changed = curAdap.update(newAdap)
        if not changed:
            print(f'no important change in {repr(curAdap)}')
            return
        # Updating the NetAdapsView...
        self._adapsvw.changeAdap(curAdap, adapIdx)
        #
        self._refreshInfoWin(adapIdx)
    
    def _onNetAdapCreated(self, _: tk.Event) -> None:
        newAdap = self._qAdapChange.get()
        try:
            self._acbag.indexAdap(newAdap)
            logging.error(
                '%s was ceated while has already loaded into the bag.',
                newAdap,)
            return
        except ValueError:
            logging.error(
                '%s was changed while has a contradictory peer in the bag.',
                newAdap,)
            return
        except IndexError:
            pass
        self._acbag.addAdap(newAdap)
        adapIdx = self._acbag.indexAdap(newAdap)
        self._adapsvw.addAdap(newAdap, adapIdx)

    def _onNetAdapDeleted(self, _: tk.Event) -> None:
        delAdap = self._qAdapDeletion.get()
        try:
            adapIdx = self._acbag.indexAdap(delAdap)
        except (IndexError, ValueError):
            logging.info(
                '%s was deleted while has not loaded into the bag.',
                delAdap,)
            return
        # Closing its info win if any...
        self._closeInfoWin(adapIdx)
        #
        vwIdx = self._adapsvw.getSelectedIdx()
        if vwIdx is not None and vwIdx.getAdap() == adapIdx:
            self._ipsvw.clear()
        #
        self._adapsvw.delIdx(adapIdx)
    
    def _onNetConfigChanged(self, _: tk.Event) -> None:
        newConfig = self._qConfigChange.get()
        try:
            configIdx = self._acbag.indexConfig(newConfig)
        except IndexError:
            logging.info(
                '%s changed but has not loaded into the App.',
                newConfig,)
            return
        curConfig: NetConfig = self._acbag[configIdx] # type: ignore
        # Updating `_acbag`...`
        changed = curConfig.update(newConfig)
        if not changed:
            logging.info(f'no important change in {repr(newConfig)}')
            return
        # Updaing its info win if any...
        self._refreshInfoWin(configIdx)
        # Updating the adaps view...
        self._adapsvw.changeConfig(newConfig, configIdx)
        adapIdx = configIdx.getAdap()
        adap: NetAdap = self._acbag[adapIdx] # type: ignore
        self._adapsvw.changeAdap(adap, adapIdx)
        # Updating IpsView...
        vwIdx = self._getNetItemIdx()
        if vwIdx is not None and (vwIdx == configIdx or
                vwIdx == configIdx.getAdap()):
            self._ipsvw.populate(newConfig, self._mpNameDns.values())
    
    def _onNetConfigCreated(self, _: tk.Event) -> None:
        newConfig = self._qConfigCreation.get()
        try:
            self._acbag.indexConfig(newConfig)
            logging.error(
                '%s was ceated while has already loaded into the bag.',
                newConfig,)
            return
        except ValueError:
            logging.error(
                '%s was changed while has a contradictory peer in the bag.',
                newConfig,)
            return
        except IndexError:
            pass
        # Adding config to the bag...
        try:
            self._acbag.addConfig(newConfig)
        except ValueError:
            # No corresonding adapter, returning...
            return
        # Adding to the AdapsView...
        configIdx = self._acbag.indexConfig(newConfig)
        self._adapsvw.addConfig(newConfig, configIdx)

    def _onNetConfigDeleted(self, _: tk.Event) -> None:
        delConfig = self._qConfigChange.get()
        try:
            configIdx = self._acbag.indexConfig(delConfig)
        except IndexError:
            logging.info(
                '%s was deleted does and has not loaded into the App.',
                delConfig,)
            return
        # Removing from the bag...
        self._acbag.delIdx(configIdx)
        # Closing its info win if any...
        try:
            infoWin = self._infoWins[configIdx]
        except KeyError:
            pass
        else:
            infoWin.closeWin()
        # Updating IpsView...
        vwIdx = self._getNetItemIdx()
        if vwIdx is not None:
            if vwIdx == configIdx:
                self._ipsvw.clear()
            elif vwIdx == configIdx.getAdap():
                self._ipsvw.populate(
                    self._acbag[vwIdx],
                    self._mpNameDns.values(),)
        #
        self._adapsvw.delIdx(configIdx)
    
    def _initViews(self) -> None:
        """Initializes the interface view and the """
        self._readNetAdaps()
        self._readDnses()
    
    def _readDnsInfo(self, idx: ACIdx | None) -> None:
        if idx is None:
            self._lfrm_ips.config(text='')
            self._ipsvw.clear()
            return
        adap: NetAdap = self._acbag[idx.getAdap()] # type: ignore
        self._lfrm_ips.config(
            text=adap.NetConnectionID)
        self._ipsvw.populate(
            adap,
            self._mpNameDns.values(),
            idx.cfgIdx)

    def _readNetAdaps(self) -> None:
        """Reads network interfaces."""
        from utils.funcs import readNetAdaps
        self._asyncMngr.InitiateOp(
            start_cb=readNetAdaps,
            finish_cb=self._onNetAdapsRead,
            widgets=(self._adapsvw,))
    
    def _onNetAdapsRead(self, fut: Future[AdapCfgBag]) -> None:
        try:
            self._acbag = fut.result()
            self._adapsvw.populate(self._acbag)
        except CancelledError:
            self._msgvw.AddMessage(
                _('X_CANCELED').format(_('READING_INTERFACES')),
                type_=MessageType.INFO)
        else:
            # Running WMI monitoring thread...
            try:
                self._netItemThrd
                return
            except AttributeError:
                self._netItemThrd = NetItemMonitor(
                    self,
                    self._qAdapChange,
                    self._qAdapCreation,
                    self._qAdapDeletion,
                    self._qConfigChange,
                    self._qConfigCreation,
                    self._qConfigDeletion,)
                self._netItemThrd.start()
    
    def _readDnses(self) -> None:
        from utils.funcs import listDnses
        self._asyncMngr.InitiateOp(
            start_cb=listDnses,
            start_args=(self._db,),
            finish_cb=self._onDnsesRead)

    def _onDnsesRead(
            self,
            fut: Future[tuple[dict[str, DnsServer], dict[
                IPv4 | IPv6, DnsServer]]],
            ) -> None:
        try:
            self._mpNameDns, self._mpIpDns = fut.result()
            self._dnsvw.populate(self._mpNameDns.values())
        except CancelledError:
            self._msgvw.AddMessage(
                _('X_CANCELED').format(_('READING_DNSES')),
                type_=MessageType.INFO)
    
    def _getNetItemIdx(self) -> ACIdx | None:
        """Gets the selected WMI network item (either adapter or
        configuration) index. If nothing is selected, it informs the user
        and returns `None`.
        """
        idx = self._adapsvw.getSelectedIdx()
        if idx is None:
            self._msgvw.AddMessage(
                _('SELECT_ITEM_INTER_VIEW'),
                type_=MessageType.WARNING)
            return
        return idx
    
    def _showInfoWin(self, idx: ACIdx | None = None) -> None:
        # Getting selected item in the NetAdapsView...
        if idx is None:
            idx = self._getNetItemIdx()
            if idx is None:
                return
        # 
        if idx in self._infoWins:
            self._infoWins[idx].focus_set()
            self._infoWins[idx].grab_set()
            return
        #
        infoWin = NetItemInfoWin(
            self,
            self._acbag,
            idx,
            self._onInfoWinClosed,
            xy=(self._settings.nid_x, self._settings.nid_y,),
            width=self._settings.nid_width,
            height=self._settings.nid_height,
            key_width=self._settings.nid_key_width,
            value_width=self._settings.nid_value_width,)
        self._infoWins[idx] = infoWin
        infoWin.showWin()
    
    def _closeInfoWin(self, idx: ACIdx) -> None:
        try:
            infoWin = self._infoWins[idx]
        except KeyError:
            pass
        else:
            infoWin.closeWin()
    
    def _refreshInfoWin(self, idx: ACIdx) -> None:
        try:
            infoWin = self._infoWins[idx]
        except KeyError:
            pass
        else:
            infoWin.populateInfo()
    
    def _onInfoWinClosed(self, idx: ACIdx) -> None:
        try:
            infoWin = self._infoWins[idx]
            del self._infoWins[idx]
        except KeyError:
            logging.error(
                'an attempt to close an info window but index does not exist\n%s',
                idx,
                stack_info=True,)
            return
        self._grabInoWinSettings(infoWin)
    
    def _grabInoWinSettings(self, info_win: NetItemInfoWin) -> None:
        """Grabs settings for a `NetItemInfoWin` to save into the
        `_settings` attribute.
        """
        nidSettings = info_win.settings
        self._settings.nid_x = nidSettings.x
        self._settings.nid_y = nidSettings.y
        self._settings.nid_width = nidSettings.width
        self._settings.nid_height = nidSettings.height
        self._settings.nid_key_width = nidSettings.key_width
        self._settings.nid_value_width = nidSettings.value_int

    def _onDnsApplied(self, fut: Future[None]) -> None:
        try:
            fut.result()
        except CancelledError:
            self._msgvw.AddMessage(
                _('X_CANCELED').format(_('SETTING_DNS')),
                type_=MessageType.INFO)
        else:
            self._readDnsInfo(self._adapsvw.getSelectedIdx())

    def _addDns(self) -> None:
        from .dns_dialog import DnsDialog
        dnsDialog = DnsDialog(self, self._mpNameDns, self._mpIpDns)
        dns = dnsDialog.showDialog()
        if dns is None:
            return
        # Adding DNS server...
        for ip in dns.toSet():
            self._mpIpDns[ip] = dns
        self._mpNameDns[dns.name] = dns
        self._db.insertDns(dns)
        self._dnsvw.appendDns(dns)
    
    def _deleteDns(self) -> None:
        from tkinter.messagebox import askyesno
        names = self._dnsvw.getSelectedNames()
        if len(names) != 1:
            self._msgvw.AddMessage(
                _('SELECT_ONE_ITEM_DNS_VIEW'),
                type_=MessageType.WARNING)
            return
        dnsName = names[0]
        response = askyesno(message=_('CONFIRM_DEL_DNS').format(dnsName))
        if response is False:
            return
        ipsSet = self._mpNameDns[dnsName].toSet()
        del self._mpNameDns[dnsName]
        for ip in ipsSet:
            del self._mpIpDns[ip]
        self._db.deleteDns(dnsName)
        self._dnsvw.deleteName(dnsName)
    
    def _editDns(self) -> None:
        from .dns_dialog import DnsDialog
        from utils.funcs import mergeMsgs
        names = self._dnsvw.getSelectedNames()
        if len(names) != 1:
            self._msgvw.AddMessage(
                _('SELECT_ONE_ITEM_DNS_VIEW'),
                type_=MessageType.WARNING)
            return
        dnsOldName = names[0]
        dnsOldIps = self._mpNameDns[dnsOldName].toIpTuple()
        mpNameDnsCpy = self._mpNameDns.copy()
        del mpNameDnsCpy[dnsOldName]
        mpIpDnsCpy = self._mpIpDns.copy()
        for ip in dnsOldIps:
            del mpIpDnsCpy[ip]
        dnsDialog = DnsDialog(
            self,
            mpNameDnsCpy,
            mpIpDnsCpy,
            self._mpNameDns[dnsOldName])
        newDns = dnsDialog.showDialog()
        if (newDns is None) or (newDns.name == dnsOldName and
                newDns.toIpTuple() == dnsOldIps):
            # No change, doing nothing...
            return
        # Applying change...
        self._mpNameDns = mpNameDnsCpy
        self._mpNameDns[newDns.name] = newDns
        self._mpIpDns = mpIpDnsCpy
        for ip in dnsOldIps:
            self._mpIpDns[ip] = newDns
        self._dnsvw.changeDns(dnsOldName, newDns)
        self._db.updateDns(dnsOldName, newDns)
    
    def _setIps(self) -> None:
        # Reading network interface index...
        netIntIdx = self._getNetItemIdx()
        if netIntIdx is None:
            return
        try:
            ips = self._dnsvw.getIps()
        except ValueError:
            self._msgvw.AddMessage(
                'Select IPs individually or entire rows.',
                type_=MessageType.ERROR)
            return
        code = self._acbag[netIntIdx].setDnsSearchOrder(ips)
        if code != NetConfigCode.SUCCESSFUL:
            self._msgvw.AddMessage(code.name)
    
    def _testUrl(self) -> None:
        # Reading network interface name...
        idx = self._getNetItemIdx()
        if idx is None:
            return
        #
        from widgets.url_dialog import UrlDialog
        dnsDialog = UrlDialog(
            self,
            self._acbag[idx].NetConnectionID,
            self._mpNameDns,
            self._IMG_GTICK,
            self._IMG_REDX,
            self._IMG_ARROW,
            self._GIF_DWAIT)
        dns = dnsDialog.showDialog()
        if dns is None:
            return
