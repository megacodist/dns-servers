#
# 
#

from os import PathLike
import tkinter as tk
from tkinter import ttk
from typing import Callable, NamedTuple, TYPE_CHECKING


if TYPE_CHECKING:
    _: Callable[[str], str]


class LucenseDlgSettings(NamedTuple):
    x: int
    y: int
    width: int
    height: int


class LicenseDialog(tk.Toplevel):
    def __init__(
            self,
            master: tk.Misc,
            lic_file: str | PathLike,
            *,
            xy: tuple[int, int] | None = None,
            width: int = 400,
            height: int = 350,
            ) -> None:
        super().__init__(master)
        self.title(_('LICENSE'))
        self.resizable(True, True)
        self.geometry(f'{width}x{height}')
        # Loading License Dialog (LD) settings...
        settings = self._ReadSettings()
        self.geometry(
            f'{settings["LD_WIDTH"]}x{settings["LD_HEIGHT"]}'
            + f'+{settings["LD_X"]}+{settings["LD_Y"]}')
        self.state(settings['LD_STATE'])
        # Making this dialog as modal...
        self.grab_set()
        self.transient()
        # Initializing GUI...
        self._hscrllbr = ttk.Scrollbar(
            self,
            orient='horizontal')
        self._vscrllbr = ttk.Scrollbar(
            self,
            orient='vertical')
        self._txt = tk.Text(
            self,
            wrap='none')
        self._hscrllbr.config(
            command=self._txt.xview)
        self._vscrllbr.config(
            command=self._txt.yview)
        self._txt.config(
            xscrollcommand=self._hscrllbr.set,
            yscrollcommand=self._vscrllbr.set)
        self._hscrllbr.pack(
            side='bottom',
            fill='x')
        self._vscrllbr.pack(
            side='right',
            fill='y')
        self._txt.pack(
            fill='both',
            side='top',
            expand=1)
        #
        with open(lic_file, 'rt') as lcnsStream:
            self._txt.insert(
                tk.END,
                '\n'.join(lcnsStream.readlines()))
        #
        if xy is None:
            self.after(10, self._centerDialog, master)
        else:
            self.geometry(f'+{xy[0]}+{xy[1]}')
        # Binding events...
        self.protocol('WM_DELETE_WINDOW', self._onClosing)
    
    def _centerDialog(self, parent: tk.Misc) -> None:
        _, x, y = parent.winfo_geometry().split('+')
        x = int(x) + (parent.winfo_width() - self.winfo_width()) // 2
        y = int(y) + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')

    def _ReadSettings(self) -> dict[str, Any]:
        # Considering License Dialog (LD) default settings...
        defaults = {
            'LD_WIDTH': 500,
            'LD_HEIGHT': 700,
            'LD_X': 200,
            'LD_Y': 200,
            'LD_STATE': 'normal',
        }
        return AppSettings().Read(defaults)

    def _onClosing(self) -> None:
        settings = {}

        # Getting the geometry of the License Dialog (LD)...
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
            settings['LD_WIDTH'] = int(match.group('width'))
            settings['LD_HEIGHT'] = int(match.group('height'))
            settings['LD_X'] = int(match.group('x'))
            settings['LD_Y'] = int(match.group('y'))
        else:
            logging.error('Cannot get the geometry of License Dialog.')

        # Getting other License Dialog (LD) settings...
        settings['LD_STATE'] = self.state()

        AppSettings().Update(settings)
        self.destroy()
