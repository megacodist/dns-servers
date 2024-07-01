#
# 
#


from typing import Any


class NetInt:
    def __init__(
            self,
            index: int,
            interface_idx: int,
            net_conn_id: str,
            description: str,
            dhcp_enabled: bool,
            dns_order: tuple[str, ...] | None,
            default_gateway: tuple[str, ...] | None,
            guid: str,
            mac_addr: str,
            ) -> None:
        self.NetConnectionID: str = net_conn_id
        """The name of the network interface in the shell."""
        self.Description: str = description
        self.DHCPEnabled: bool = dhcp_enabled
        self.DNSServerSearchOrder: tuple[str, ...] | None = dns_order
        self.DefaultIPGateway: tuple[str, ...] | None = default_gateway
        self.Index = index
        self.InterfaceIndex = interface_idx
        self.MACAddress = mac_addr
        self.GUID = guid
    
    def __repr__(self) -> str:
        return (f"<{self.__class__.__qualname__} "
            f"NetConnectionID={self.NetConnectionID} "
            f"Description={self.Description} "
            f"DHCPEnabled={self.DHCPEnabled} "
            f"DNSServerSearchOrder={self.DNSServerSearchOrder} "
            f"DefaultIPGateway={self.DefaultIPGateway}>")


def enumNetInts() -> list[NetInt]:
    """Enumerates network interfaces on this Windows platform."""
    import win32com.client
    from win32com.client import CDispatch
    wmi = win32com.client.GetObject("winmgmts:")
    # Querying network adapter configurations...
    configQuery = """
        SELECT
            Index, InterfaceIndex, MACAddress, SettingID, Description,
            DHCPEnabled, DNSServerSearchOrder, DefaultIPGateway
        FROM
            Win32_NetworkAdapterConfiguration"""
    configs = wmi.ExecQuery(configQuery)
    # Querying network adapters...
    adaptersQuery = """
        SELECT
            Index, InterfaceIndex, MACAddress, GUID, Description,
            NetConnectionID, NetEnabled
        FROM
            Win32_NetworkAdapter
        WHERE
            PhysicalAdapter=True"""
    adapters = wmi.ExecQuery(adaptersQuery)
    # Merging results...
    mpIdxCfg = dict[tuple[int, int], CDispatch]()
    missCfgs = list[CDispatch]()
    for cfg in configs:
        if not (isinstance(cfg.Index, int) and isinstance(
                cfg.InterfaceIndex, int)):
            missCfgs.append(cfg)
            continue
        mpIdxCfg[(cfg.Index, cfg.InterfaceIndex,)] = cfg
    mpIdxAdap = dict[tuple[int, int], CDispatch]()
    missAdaps = list[CDispatch]()
    for adap in adapters:
        if not (isinstance(adap.Index, int) and isinstance(
                adap.InterfaceIndex, int)):
            missAdaps.append(adap)
            continue
        mpIdxAdap[(adap.Index, adap.InterfaceIndex,)] = adap
    cmnKeys = set(mpIdxCfg.keys()).intersection(mpIdxAdap.keys())


def main() -> None:
    from pprint import pprint
    pprint(enumNetInts())


if __name__ == '__main__':
    main()
