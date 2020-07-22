"""Torrent Peer."""

import ipaddress
import dataclasses


@dataclasses.dataclass(frozen=True)
class TorrentPeer:
    """Torrent peer definition."""

    ip: ipaddress.IPv4Address
    port: int
