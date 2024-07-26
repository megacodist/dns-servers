#
# 
#

import logging
from queue import Queue
from threading import Event, Thread
import tkinter as tk

import pythoncom
import wmi as wmilib
from wmi import _wmi_event as WmiEvent

from ntwrk import NetAdap


class NetIntMonitor(Thread):
    def __init__(self, app_win: tk.Tk, q: Queue[WmiEvent]) -> None:
        """Initializes a new instance of this class. `app_win` is the main
        application window that responds to `<<NetIntChange>>` event.
        """
        super().__init__(
            name='Network adapters monitor thread',
            daemon=True)
        self._appTk = app_win
        self._q = q
        self._cancel: Event | None = Event()
    
    def run(self):
        query = f"""
            SELECT
                *
            FROM
                __InstanceModificationEvent
            WITHIN
                1
            WHERE
                TargetInstance ISA 'Win32_NetworkAdapterConfiguration'"""
        #
        pythoncom.CoInitialize()
        wmi = wmilib.WMI()
        watcher = wmi.watch_for(query)
        #
        while True:
            # Checking cancel is requested...
            if self._cancel.is_set(): # type: ignore
                self._cancel = None
                break
            # Looking for changes...
            try:
                event = watcher()
                self._print(event)
                self._q.put(event)
                self._appTk.event_generate('<<NetIntChange>>', when='tail',)
            except wmilib.x_wmi_timed_out:
                logging.debug('Timeout waiting for event')
            except wmilib.x_wmi as err:
                logging.debug(err)
        #
        pythoncom.CoUninitialize()
    
    def _print(self, event: WmiEvent) -> None:
        attrs = [
            attr
            for attr in dir(event.ole_object)
            if not attr.startswith('_') and not
                callable(getattr(event.ole_object, attr))]
        for attr in attrs:
            print(f'{attr}: {getattr(event.ole_object, attr)}')
    
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
