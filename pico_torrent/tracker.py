"""Torrent tracker."""

import io
import socket
import struct
import random
import requests
import ipaddress
import functools
import dataclasses

from urllib.parse import urlencode
from typing import List, Tuple, cast

from pico_torrent.bencode import BencodeDecoder, BencodeDecodeError


@dataclasses.dataclass
class TorrentPeer:
    """Torrent peer."""

    ip: ipaddress.IPv4Address
    port: int


class BadTrackerResponse(Exception):
    """Exception when tracker return non 200 http code."""


class TorrentTracker:
    """Torrent Tracker for get available peers for download."""

    def __init__(
        self,
        torrent_announce_url: str,
        torrent_info_hash: bytes,
        full_torrent_bytes: int,
    ):
        """Initialize torrent tracker client."""
        self.interval = None
        self.tracker_id = None
        self.announce_url = torrent_announce_url
        self.torrent_info_hash = torrent_info_hash
        self.full_torrent_bytes = full_torrent_bytes

    @property
    def uploaded(self) -> int:
        """Count of uploaded bytes."""
        return 0

    @property
    def downloaded(self) -> int:
        """Count of downloaded bytes."""
        return 0

    @property
    def left(self) -> int:
        """Count of bytes left for download full torrent file."""
        return self.full_torrent_bytes - self.downloaded

    @functools.cached_property
    def port(self) -> int:
        """Port of peer."""
        return random.randint(6881, 6889)  # noqa: S311

    @functools.cached_property
    def peer_id(self) -> str:
        """Peer ID for current torrent download session."""
        prefix = '-PT{}-'.format(
            ''.join(str(random.randint(0, 9)) for _ in range(4)),  # noqa: S311
        )
        number = ''.join(
            str(random.randint(0, 9)) for _ in range(12)  # noqa: S311
        )

        return prefix + number

    def _get_url_for_fetch_available_peers(self, first: bool = False) -> str:
        """Return url for fetch available peers from announce tracker."""
        params = {
            "info_hash": self.torrent_info_hash,
            "peer_id": self.peer_id,
            "port": self.port,
            "uploaded": self.uploaded,
            "downloaded": self.downloaded,
            "left": self.left,
            "compact": 1,
        }

        if first:
            params['event'] = 'started'

        if self.tracker_id:
            params['trackerid'] = self.tracker_id

        return self.announce_url + '?' + urlencode(params)

    def get_available_peers(self) -> List[TorrentPeer]:
        """Fetch available peers from announce."""
        request_url = self._get_url_for_fetch_available_peers(
            first=True if not self.tracker_id else False,
        )
        tracker_response = requests.get(request_url)

        if tracker_response.status_code != 200:
            raise BadTrackerResponse(tracker_response.content)

        decoder = BencodeDecoder(io.BytesIO(tracker_response.content))

        try:
            decoded_content: dict = cast(dict, decoder.decode())
        except BencodeDecodeError:
            raise BadTrackerResponse("malformed response")

        if b'faliure reason' in decoded_content:
            raise Exception(decoded_content[b'faliure reason'].decode())

        self.interval = decoded_content[b'interval']
        self.tracker_id = decoded_content.get(b'tracker id', None)

        raw_peers = decoded_content[b'peers']

        if len(raw_peers) % 6 != 0:
            raise BadTrackerResponse('get malformed peers')

        fetched_peers = []

        for index in range(0, len(raw_peers), 6):
            raw_peer_bytes = raw_peers[index:index+6]

            ip_bytes = raw_peer_bytes[:4]
            port_bytes = raw_peer_bytes[4:]

            ip = ipaddress.IPv4Address(socket.inet_ntoa(ip_bytes))
            port, *_ = cast(Tuple[int, ...], struct.unpack('>H', port_bytes))

            peer = TorrentPeer(ip=ipaddress.IPv4Address(ip), port=port)
            fetched_peers.append(peer)

        return fetched_peers
