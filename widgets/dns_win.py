#
# 
#

import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import PIL.Image
import PIL.ImageTk

from .dns_view import Dnsview
from .interface_view import InterfaceView
from .message_view import MessageView, MessageType
from utils.settings import AppSettings
from utils.types import TkImg


class DnsWin(tk.Tk):
    def __init__(self, res_dir: Path, settings: AppSettings) -> None:
        super().__init__(
            screenName=None,
            baseName=None,
            className='McDns',
            useTk=True,
            sync=False,
            use=None)
        self.title('DNS server manager')
        self.geometry(f'{settings.win_width}x{settings.win_height}+'
            f'{settings.win_x}+{settings.win_y}')
        #
        self._RES_DIR = res_dir
        """The directory of the resources."""
        self._settings = settings
        """The application settings object."""
        # Images...
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
        # Bindings & events...
        self.protocol('WM_DELETE_WINDOW', self._OnWinClosing)
    
    def _loadRes(self) -> None:
        # Loading 'close.png...
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
        self._btn_removeDns = ttk.Button(
            self._frm_dnsButns,
            image=self._IMG_REMOVE) # type: ignore
        self._btn_removeDns.pack(
            side=tk.LEFT)
        #
        self._btn_editDns = ttk.Button(
            self._frm_dnsButns,
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
        self._dnsvw = Dnsview(self._lfrm_dnses)
        self._dnsvw.grid(
            column=0,
            row=1,
            sticky=tk.NSEW,)
        #
        self._msgvw = MessageView(self._pdwin, self._IMG_CLOSE)
        self._msgvw.pack(fill=tk.BOTH, expand=1)
        self._pdwin.add(self._msgvw, weight=1)
    
    def _readInterfaces(self) -> None:
        from ntwrk import GetInterfacesNames
        try:
            for name in GetInterfacesNames():
                pass
        except TypeError as err:
            self._msgvw.AddMessage(
                str(err),
                title=err.__class__.__qualname__,
                type_=MessageType.ERROR)
    
    def _OnWinClosing(self) -> None:
        # Releasing images...
        self._HIMG_CLOSE.close()
        self._HIMG_ADD.close()
        self._HIMG_REMOVE.close()
        self._HIMG_EDIT.close()
        self._HIMG_APPLY.close()
        #
        self._saveGeometry()
        self._settings.left_panel_width = self._pdwin.sashpos(0)
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

    def _addDns(self) -> None:
        from .dns_dialog import DnsDialog
        a = DnsDialog(self)
        print(a.result)
