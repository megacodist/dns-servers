#
# 
#

from pathlib import Path
import tkinter as tk
from tkinter import ttk

import PIL.Image
import PIL.ImageTk

from .interface_view import InterfaceView
from .message_view import MessageView
from utils.types import TkImg


class DnsWin(tk.Tk):
    def __init__(self, res_dir: Path) -> None:
        super().__init__(
            screenName=None,
            baseName=None,
            className='McDns',
            useTk=True,
            sync=False,
            use=None)
        self.title('DNS server manager')
        #
        self._RES_DIR = res_dir
        """The directory of the resources."""
        # Images...
        self._HIMG_CLOSE: PIL.Image.Image
        self._IMG_CLOSE: TkImg
        # Loading resources...
        self._loadRes()
        # Initializing the GUI...
        self._initGui()
        # Bindings & events...
        self.protocol('WM_DELETE_WINDOW', self._OnWinClosing)
    
    def _loadRes(self) -> None:
        # Loading 'close.png...
        self._HIMG_CLOSE = PIL.Image.open(self._RES_DIR / 'close.png')
        self._HIMG_CLOSE = self._HIMG_CLOSE.resize(size=(16, 16,))
        self._IMG_CLOSE = PIL.ImageTk.PhotoImage(image=self._HIMG_CLOSE)
    
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
            text='Interfaces')
        self._lfrm_interfaces.grid(
            column=0,
            row=0,
            padx=3,
            pady=3,
            sticky=tk.NSEW,)
        #
        self._intervw = InterfaceView(self._lfrm_interfaces)
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
        self._lbl_primary = ttk.Label(self._lfrm_interDnses, text='Primary')
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
            text='Secondary')
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
            text='DNS servers')
        self._lfrm_dnses.columnconfigure(0, weight=1)
        self._lfrm_dnses.rowconfigure(0, weight=1)
        self._lfrm_dnses.grid(
            column=0,
            row=1,
            padx=3,
            pady=3,
            sticky=tk.NSEW,)
        #
        self._trvw_dnses = ttk.Treeview(self._lfrm_dnses)
        self._trvw_dnses.grid(
            column=0,
            row=0,
            sticky=tk.NSEW,)
        #
        self._frm_dnsButns = tk.Frame(self._lfrm_dnses)
        self._frm_dnsButns.grid(
            column=0,
            row=1,
            sticky=tk.NSEW,)
        #
        self._btn_changeDns = ttk.Button(self._frm_dnsButns, text='Change')
        self._btn_changeDns.pack(
            side=tk.RIGHT)
        #
        self._btn_removeDns = ttk.Button(self._frm_dnsButns, text='Remove')
        self._btn_removeDns.pack(
            side=tk.RIGHT)
        #
        self._btn_addDns = ttk.Button(self._frm_dnsButns, text='Add')
        self._btn_addDns.pack(
            side=tk.RIGHT)
        #
        self._msgvw = MessageView(self._pdwin, self._IMG_CLOSE)
        self._msgvw.pack(fill=tk.BOTH, expand=1)
        self._pdwin.add(self._msgvw, weight=1)
    
    def _OnWinClosing(self) -> None:
        # Releasing images...
        self._HIMG_CLOSE.close()
        # Destroying the window...
        self.destroy()
