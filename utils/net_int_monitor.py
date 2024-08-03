#
# 
#

import logging
from queue import Queue
from threading import Event, Thread
import tkinter as tk
from typing import Any

import pythoncom
import wmi

from ntwrk import NetAdap, NetConfig


class NetIntMonitor(Thread):
    def __init__(
            self,
            app_win: tk.Tk,
            adap_change: Queue[NetAdap],
            adap_creation: Queue[NetAdap],
            adap_deletion: Queue[NetAdap],
            confgi_change: Queue[NetConfig],
            config_creation: Queue[NetAdap],
            config_deletion: Queue[NetAdap],
            ) -> None:
        """Initializes a new instance of this class. `app_win` is the main
        application window that handle the following events:
        * `<<NetAdapChanged>>`
        * `<<NetAdapCreated>>`
        * `<<NetAdapDeleted>>`
        * `<<NetConfigChanged>>`
        * `<<NetConfigCreated>>`
        * `<<NetConfigDeleted>>`
        """
        super().__init__(
            name='Network adapters monitor thread',
            daemon=True)
        self._appTk = app_win
        self._qAdapChange = adap_change
        self._qAdapCreation = adap_creation
        self._qAdapDeletion = adap_deletion
        self._qConfigChange = confgi_change
        self._qConfigCreation = config_creation
        self._qConfigDeletion = config_deletion
        self._cancel: Event | None = Event()
    
    def run(self):
        adapChangeQuery = f"""
            SELECT *
            FROM __InstanceModificationEvent
            WITHIN 1
            WHERE TargetInstance ISA 'Win32_NetworkAdapter'"""
        adapCreationQuery = """
            SELECT *
            FROM __InstanceCreationEvent
            WITHIN 1
            WHERE TargetInstance ISA 'Win32_NetworkAdapter'"""
        adapDeletionQuery = """
            SELECT *
            FROM __InstanceDeletionEvent
            WITHIN 1
            WHERE TargetInstance ISA 'Win32_NetworkAdapter'"""
        configChangeQuery = f"""
            SELECT *
            FROM __InstanceModificationEvent
            WITHIN 1
            WHERE TargetInstance ISA 'Win32_NetworkAdapterConfiguration'"""
        configCreationQuery = """
            SELECT *
            FROM __InstanceCreationEvent
            WITHIN 1
            WHERE TargetInstance ISA 'Win32_NetworkAdapterConfiguration'"""
        configDeletionQuery = """
            SELECT *
            FROM __InstanceDeletionEvent
            WITHIN 1
            WHERE TargetInstance ISA 'Win32_NetworkAdapterConfiguration'"""
        #
        pythoncom.CoInitialize()
        wmi_ = wmi.WMI()
        adapChangeWatcher = wmi_.watch_for(adapChangeQuery)
        adapCreationWatcher = wmi_.watch_for(adapCreationQuery)
        adapDeletionWatcher = wmi_.watch_for(adapDeletionQuery)
        configChangeWatcher = wmi_.watch_for(configChangeQuery)
        configCreationWatcher = wmi_.watch_for(configCreationQuery)
        configDeletionWatcher = wmi_.watch_for(configDeletionQuery)
        #
        while True:
            # Checking cancel is requested...
            if self._cancel.is_set(): # type: ignore
                self._cancel = None
                break
            # Looking for adapter changes...
            try:
                event = adapChangeWatcher()
                try:
                    self._qAdapChange.put(NetAdap(event.ole_object))
                    self._appTk.event_generate(
                        '<<NetAdapChanged>>',
                        when='tail',)
                except TypeError:
                    logging.debug('failed to catch NetAdap change')
            except wmi.x_wmi_timed_out:
                logging.debug('Timeout waiting for event')
            except wmi.x_wmi as err:
                logging.debug(err)
            # Looking for adapter creations...
            try:
                event = adapChangeWatcher()
                try:
                    self._qAdapCreation.put(NetAdap(event.ole_object))
                    self._appTk.event_generate(
                        '<<NetAdapCreated>>',
                        when='tail',)
                except TypeError:
                    logging.debug('failed to catch NetAdap creation')
            except wmi.x_wmi_timed_out:
                logging.debug('Timeout waiting for event')
            except wmi.x_wmi as err:
                logging.debug(err)
            # Looking for adapter deletion...
            try:
                event = adapDeletionWatcher()
                try:
                    self._qAdapDeletion.put(NetAdap(event.ole_object))
                    self._appTk.event_generate(
                        '<<NetAdapDeleted>>',
                        when='tail',)
                except TypeError:
                    logging.debug('failed to catch NetAdap deletion')
            except wmi.x_wmi_timed_out:
                logging.debug('Timeout waiting for event')
            except wmi.x_wmi as err:
                logging.debug(err)
            # Looking for configuration changes...
            try:
                event = configChangeWatcher()
                try:
                    self._qConfigChange.put(NetConfig(event.ole_object))
                    self._appTk.event_generate(
                        '<<NetConfigChanged>>',
                        when='tail',)
                except TypeError:
                    logging.debug('failed to catch NetConfig change')
            except wmi.x_wmi_timed_out:
                logging.debug('Timeout waiting for event')
            except wmi.x_wmi as err:
                logging.debug(err)
            # Looking for configuration creation...
            try:
                event = configCreationWatcher()
                try:
                    self._qConfigCreation.put(NetConfig(event.ole_object))
                    self._appTk.event_generate(
                        '<<NetConfigCreated>>',
                        when='tail',)
                except TypeError:
                    logging.debug('failed to catch NetConfig creation')
            except wmi.x_wmi_timed_out:
                logging.debug('Timeout waiting for event')
            except wmi.x_wmi as err:
                logging.debug(err)
        #
        pythoncom.CoUninitialize()
    
    def _print(self, event: Any) -> None:
        attrs = [
            attr
            for attr in dir(event)
            if not attr.startswith('_') and not
                callable(getattr(event, attr))]
        for attr in attrs:
            print(f'{attr}: {getattr(event, attr)}')
    
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
