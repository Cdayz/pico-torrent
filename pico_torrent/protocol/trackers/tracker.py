"""Torrent tracker."""

import io
import socket
import struct
import requests
import ipaddress

from urllib.parse import urlencode
from typing import List, Tuple, cast

from pico_torrent.protocol.peers.peer import TorrentPeer
from pico_torrent.protocol.bencode import BencodeDecoder, BencodeDecodeError


class BadTrackerResponse(Exception):
    """Exception when tracker return non 200 http code."""


class TorrentTracker:
    """Torrent Tracker for get available peers for download."""

    def __init__(
        self,
        torrent_announce_url: str,
        torrent_info_hash: bytes,
        full_torrent_bytes: int,
        this_peer_listen_port: int,
        this_peer_id: str,
    ):
        """Initialize torrent tracker client."""
        self.interval = None
        self.tracker_id = None
        self.announce_url = torrent_announce_url
        self.torrent_info_hash = torrent_info_hash
        self.full_torrent_bytes = full_torrent_bytes
        # Some useful stats for tracker
        self.uploaded = 0
        self.downloaded = 0
        # Information about this peer
        self.this_peer_port = this_peer_listen_port
        self.this_peer_id = this_peer_id

    @property
    def left(self) -> int:
        """Count of bytes left for download full torrent file."""
        return self.full_torrent_bytes - self.downloaded

    def _get_url_for_fetch_available_peers(self, first: bool = False) -> str:
        """Return url for fetch available peers from announce tracker."""
        params = {
            "info_hash": self.torrent_info_hash,
            "peer_id": self.this_peer_id,
            "port": self.this_peer_port,
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
