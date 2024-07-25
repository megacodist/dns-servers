#
# 
#

from queue import Queue
from threading import Event, Thread
import tkinter as tk



class NetIntMonitor(Thread):
    def __init__(self, app_win: tk.Tk, q: Queue) -> None:
        """Initializes a new instance of this class. `app_win` is the main
        application window that responds to `<<NetIntChange>>` event.
        """
        super().__init__(
            name='Network adapters monitor thread',
            daemon=True)
        self._appWin = app_win
        self._q = q
        self._cancel: Event | None = Event()
    
    def run(self):
        import pythoncom
        import wmi as wmilib
        query = """
            SELECT
                *
            FROM
                __InstanceModificationEvent
            WITHIN
                1
            WHERE
                TargetInstance ISA 'Win32_NetworkAdapterConfiguration'"""
        pythoncom.CoInitialize()
        wmi = wmilib.WMI()
        watcher = wmi.watch_for(query)
        while True:
            # Checking cancel is requested...
            if self._cancel.is_set(): # type: ignore
                self._cancel = None
                break
            # Looking for changes...
            try:
                event = watcher()
                self._q.put(event)
                self._appWin.event_generate(
                    '<<NetIntChange>>',
                    when='tail',)

            except wmilib.x_wmi_timed_out:
                print("Timeout waiting for event")
            except KeyboardInterrupt:
                break
        pythoncom.CoUninitialize()
    
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
