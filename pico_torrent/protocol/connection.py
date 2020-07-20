"""Peer-to-Peer connection protocol."""

from typing import Type, Dict

from pico_torrent.protocol import messages
from pico_torrent.tracker import TorrentPeerInfo
from pico_torrent.protocol.abstract import BasePeerMessage
from pico_torrent.protocol.raw_message import PeerMessageId


MESSAGES: Dict[PeerMessageId, Type[BasePeerMessage]] = {
    PeerMessageId.Choke: messages.Choke,
    PeerMessageId.Unchoke: messages.Unchoke,
    PeerMessageId.Interested: messages.Interested,
    PeerMessageId.NotInterested: messages.NotInterested,
    PeerMessageId.Have: messages.Have,
    PeerMessageId.BitField: messages.BitField,
    PeerMessageId.Request: messages.Request,
    PeerMessageId.Piece: messages.Piece,
    PeerMessageId.Cancel: messages.Cancel,
    PeerMessageId.Port: messages.Port,
    PeerMessageId.KeepAlive: messages.KeepAlive,
    PeerMessageId.Handshake: messages.Handshake,
}


class P2PConnection:
    """Peer-to-Peer connection."""

    def __init__(self, peer: TorrentPeerInfo):
        """Initialize peer-to-peer connection."""
        pass

    def receive(self) -> BasePeerMessage:
        """Receive message from remote peer."""
        pass

    def send(self, message: BasePeerMessage):
        """Send message to remote peer."""
        pass
