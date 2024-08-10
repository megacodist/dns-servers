#
# 
#

from . import types as types_module


class AppSettings(types_module.AppSettings):
    # App window size & position...
    win_x = 100
    win_y = 100
    win_width = 600
    win_height = 450
    # Panedwindow sashes...
    net_int_ips_width = 220
    net_int_height = 250
    msgs_height = 300
    urls_width = 250
    # Columns widht...
    name_col_width = 100
    prim_4_col_width = 100
    secon_4_col_width = 100
    prim_6_col_width = 100
    secon_6_col_width = 100
    # NetItemInfoWin...
    nid_x = 200
    nid_y = 200
    nid_width = 400
    nid_height = 300
    nid_key_width = 150
    nid_value_width = 180
    # License window settings...
    licw_x = 200
    licw_y = 150
    licw_width = 400
    licw_height = 300
