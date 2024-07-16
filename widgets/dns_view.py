#
# 
#

import logging
import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, TYPE_CHECKING

import tksheet

from db import DnsServer


if TYPE_CHECKING:
    _: Callable[[str], str] = lambda a: a


class Dnsview(tksheet.Sheet):
    def __init__(
            self,
            master: tk.Misc,
            double_clicked_cb: Callable[[], None] | None = None,
            *,
            name_col_width: int = 100,
            prim_4_col_width: int = 100,
            secon_4_col_width: int = 100,
            prim_6_col_width: int = 100,
            secon_6_col_width: int = 100,
            **kwargs
            ) -> None:
        super().__init__(master, **kwargs)
        self.headers([
            _('NAME'),
            _('PRIM_4'),
            _('SECON_4'),
            _('PRIM_6'),
            _('SECON_6'),])
        self.column_width(0, name_col_width)
        self.column_width(1, prim_4_col_width)
        self.column_width(2, secon_4_col_width)
        self.column_width(3, prim_6_col_width)
        self.column_width(4, secon_6_col_width)
        #
        self._mpNameRow = dict[str, int]()
        """The mapping between DNS name and row index:

        `name -> index`
        """
        self._cbDoubleClicked = double_clicked_cb
        """The callback to be called if an item is double clicked."""
        # Bindins...
        self.enable_bindings(
            'single_select',
            'drag_select',
            'select_all',
            'column_select',
            'row_select',
            'ctrl_click_select',
            'up',
            'down',
            'left',
            'right',
            'prior',
            'next',
            'edit_cell',
            'column_width_resize',)
        self.extra_bindings([
            ("begin_edit_cell", self._onBeginEditCell),
            ('row_select_enable', self._onBeginEditCell),])
    
    def _onBeginEditCell(self, event: tksheet.EventDataDict) -> None:
        if self._cbDoubleClicked:
            self._cbDoubleClicked()
    
    def getSelectedNames(self) -> tuple[str, ...]:
        """Gets the names of the DNS servers that have selection."""
        rows = tuple(
            sorted(list({row for row, _ in self.get_selected_cells()})))
        return tuple([self.get_cell_data(row, 0) for row in rows]) # type: ignore
    
    def getColsWidth(self) -> tuple[int, int, int, int, int]:
        """Returns the width of `name`, `prim_4`, and `secon_4`, 'prim_6',
        and 'secon_6' columns width as a 5-tuple respectively.
        """
        return tuple([int(width) for width in self.get_column_widths()]) # type: ignore

    def clear(self) -> None: # type: ignore
        """Clears all DNS servers from the View."""
        count = len(self.get_sheet_data())
        for idx in reversed(range(count)):
            self.delete_row(idx)
    
    def populate(self, dnses: Iterable[DnsServer]) -> None:
        self.clear()
        for idx, dns in enumerate(dnses):
            self.insert_row(
                [dns.name, dns.prim_4, dns.secon_4, dns.prim_6, dns.secon_6])
            self._mpNameRow[dns.name] = idx
    
    def changeDns(self, dns_name: str, new_dns: DnsServer) -> None:
        row = self._mpNameRow[dns_name]
        self.set_row_data(
            row,
            [
                new_dns.name,
                new_dns.prim_4,
                new_dns.secon_4,
                new_dns.prim_6,
                new_dns.secon_6])
    
    def appendDns(self, dns: DnsServer) -> None:
        self.insert_row(
            [dns.name, dns.prim_4, dns.secon_4, dns.prim_6, dns.secon_6])
        self._mpNameRow[dns.name] = idx
        self.get_total_rows()
