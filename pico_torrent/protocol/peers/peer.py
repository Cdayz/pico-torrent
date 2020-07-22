"""Torrent Peer."""

import ipaddress
import dataclasses


@dataclasses.dataclass
class TorrentPeer:
    """Torrent peer definition."""

    ip: ipaddress.IPv4Address
    port: int