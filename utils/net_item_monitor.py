#
# 
#

import logging
from queue import Queue
from threading import Event, Thread
import tkinter as tk

import pythoncom
import wmi

from ntwrk import NetAdap, NetConfig


class NetItemMonitor:
    def __init__(
            self,
            app_win: tk.Tk,
            adap_change: Queue[NetAdap],
            adap_creation: Queue[NetAdap],
            adap_deletion: Queue[NetAdap],
            config_change: Queue[NetConfig],
            config_creation: Queue[NetConfig],
            config_deletion: Queue[NetConfig],
            ) -> None:
        self._appTk = app_win
        self._qAdapChange = adap_change
        self._qAdapCreation = adap_creation
        self._qAdapDeletion = adap_deletion
        self._qConfigChange = config_change
        self._qConfigCreation = config_creation
        self._qConfigDeletion = config_deletion
        self._thrds = list[Thread]()
        self._closeSig = Event()
    
    def start(self) -> None:
        #
        self._thrds.append(Thread(
            name='NetAdap change watcher thread',
            target=_watchAdapChange,
            args=(self._appTk, self._qAdapChange, self._closeSig),
            daemon=True,))
        #
        self._thrds.append(Thread(
            name='NetAdap creation watcher thread',
            target=_watchAdapCreation,
            args=(self._appTk, self._qAdapCreation, self._closeSig),
            daemon=True,))
        #
        self._thrds.append(Thread(
            name='NetAdap deletion watcher thread',
            target=_watchAdapDeletion,
            args=(self._appTk, self._qAdapDeletion, self._closeSig),
            daemon=True,))
        #
        self._thrds.append(Thread(
            name='NetConfig modification watcher thread',
            target=_watchConfigChange,
            args=(self._appTk, self._qConfigChange, self._closeSig),
            daemon=True,))
        #
        self._thrds.append(Thread(
            name='NetConfig creation watcher thread',
            target=_watchConfigCreation,
            args=(self._appTk, self._qConfigCreation, self._closeSig),
            daemon=True,))
        #
        self._thrds.append(Thread(
            name='NetConfig deletion watcher thread',
            target=_watchConfigDeletion,
            args=(self._appTk, self._qConfigDeletion, self._closeSig),
            daemon=True,))
        # Running threads...
        for thrd in self._thrds:
            thrd.start()

    def close(self) -> None:
        """Irreversibly closes the monitor and all its resources."""
        self._closeSig.set()


def _watchAdapChange(
        app_tk: tk.Tk,
        q: Queue[NetAdap],
        cancel: Event,
        ) -> None:
    pythoncom.CoInitialize()
    wmi_ = wmi.WMI()
    watcher = wmi_.watch_for(
        notification_type='Modification',
        wmi_class='Win32_NetworkAdapter',
        delay_secs=1,)
    while True:
        # Checking cancel is requested...
        if cancel.is_set():
            break
        # Looking for adapter changes...
        try:
            event = watcher()
            try:
                q.put(NetAdap(event.ole_object))
                app_tk.event_generate(
                    '<<NetAdapChanged>>',
                    when='tail',)
            except TypeError as err:
                logging.debug(
                    'the WMI object is inconsistent with NetAdap\n%s',
                    err)
        except wmi.x_wmi_timed_out:
            logging.debug('Timeout waiting for event')
        except wmi.x_wmi as err:
            logging.debug(err)
    pythoncom.CoUninitialize()


def _watchAdapCreation(
        app_tk: tk.Tk,
        q: Queue[NetAdap],
        cancel: Event,
        ) -> None:
    pythoncom.CoInitialize()
    wmi_ = wmi.WMI()
    watcher = wmi_.watch_for(
        notification_type='Creation',
        wmi_class='Win32_NetworkAdapter',
        delay_secs=1,)
    while True:
        # Checking cancel is requested...
        if cancel.is_set():
            break
        # Looking for adapter changes...
        try:
            event = watcher()
            try:
                q.put(NetAdap(event.ole_object))
                app_tk.event_generate(
                    '<<NetAdapCreated>>',
                    when='tail',)
            except TypeError as err:
                logging.debug(
                    'the WMI object is inconsistent with NetAdap\n%s',
                    err)
        except wmi.x_wmi_timed_out:
            logging.debug('Timeout waiting for event')
        except wmi.x_wmi as err:
            logging.debug(err)
    pythoncom.CoUninitialize()


def _watchAdapDeletion(
        app_tk: tk.Tk,
        q: Queue[NetAdap],
        cancel: Event,
        ) -> None:
    pythoncom.CoInitialize()
    wmi_ = wmi.WMI()
    watcher = wmi_.watch_for(
        notification_type='Deletion',
        wmi_class='Win32_NetworkAdapter',
        delay_secs=1,)
    while True:
        # Checking cancel is requested...
        if cancel.is_set():
            break
        # Looking for adapter changes...
        try:
            event = watcher()
            try:
                q.put(NetAdap(event.ole_object))
                app_tk.event_generate(
                    '<<NetAdapDeleted>>',
                    when='tail',)
            except TypeError as err:
                logging.debug(
                    'the WMI object is inconsistent with NetAdap\n%s',
                    err)
        except wmi.x_wmi_timed_out:
            logging.debug('Timeout waiting for event')
        except wmi.x_wmi as err:
            logging.debug(err)
    pythoncom.CoUninitialize()


def _watchConfigChange(
        app_tk: tk.Tk,
        q: Queue[NetConfig],
        cancel: Event,
        ) -> None:
    pythoncom.CoInitialize()
    wmi_ = wmi.WMI()
    watcher = wmi_.watch_for(
        notification_type='Modification',
        wmi_class='Win32_NetworkAdapterConfiguration',
        delay_secs=1,)
    while True:
        # Checking cancel is requested...
        if cancel.is_set():
            break
        # Looking for adapter changes...
        try:
            event = watcher()
            try:
                q.put(NetConfig(event.ole_object))
                app_tk.event_generate(
                    '<<NetConfigChanged>>',
                    when='tail',)
            except TypeError as err:
                logging.debug(
                    'the WMI object is inconsistent with NetConfig\n%s',
                    err)
        except wmi.x_wmi_timed_out:
            logging.debug('Timeout waiting for event')
        except wmi.x_wmi as err:
            logging.debug(err)
    pythoncom.CoUninitialize()


def _watchConfigCreation(
        app_tk: tk.Tk,
        q: Queue[NetConfig],
        cancel: Event,
        ) -> None:
    pythoncom.CoInitialize()
    wmi_ = wmi.WMI()
    watcher = wmi_.watch_for(
        notification_type='Creation',
        wmi_class='Win32_NetworkAdapterConfiguration',
        delay_secs=1,)
    while True:
        # Checking cancel is requested...
        if cancel.is_set():
            break
        # Looking for adapter changes...
        try:
            event = watcher()
            try:
                q.put(NetConfig(event.ole_object))
                app_tk.event_generate(
                    '<<NetConfigCreated>>',
                    when='tail',)
            except TypeError as err:
                logging.debug(
                    'the WMI object is inconsistent with NetConfig\n%s',
                    err)
        except wmi.x_wmi_timed_out:
            logging.debug('Timeout waiting for event')
        except wmi.x_wmi as err:
            logging.debug(err)
    pythoncom.CoUninitialize()


def _watchConfigDeletion(
        app_tk: tk.Tk,
        q: Queue[NetConfig],
        cancel: Event,
        ) -> None:
    pythoncom.CoInitialize()
    wmi_ = wmi.WMI()
    watcher = wmi_.watch_for(
        notification_type='Deletion',
        wmi_class='Win32_NetworkAdapterConfiguration',
        delay_secs=1,)
    while True:
        # Checking cancel is requested...
        if cancel.is_set():
            break
        # Looking for adapter changes...
        try:
            event = watcher()
            try:
                q.put(NetConfig(event.ole_object))
                app_tk.event_generate(
                    '<<NetConfigDeleted>>',
                    when='tail',)
            except TypeError as err:
                logging.debug(
                    'the WMI object is inconsistent with NetConfig\n%s',
                    err)
        except wmi.x_wmi_timed_out:
            logging.debug('Timeout waiting for event')
        except wmi.x_wmi as err:
            logging.debug(err)
    pythoncom.CoUninitialize()
