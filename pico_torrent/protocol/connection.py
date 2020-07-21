"""Peer-to-Peer connection protocol."""

import socket
import struct

from typing import Type, Dict

from pico_torrent.protocol import messages
from pico_torrent.tracker import TorrentPeerInfo
from pico_torrent.protocol.abstract import BasePeerMessage
from pico_torrent.protocol.raw_message import PeerMessageId, RawPeerMessage


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


class ProtocolError(Exception):
    """P2P connection protocol error."""


class P2PConnection:
    """Peer-to-Peer connection."""

    def __init__(self, peer: TorrentPeerInfo):
        """Initialize peer-to-peer connection."""
        self.peer = peer
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.handshaked = False

    def handshake(self, handshake: messages.Handshake) -> messages.Handshake:
        """Make handshake with remote peer and return handshake from remote."""
        if self.handshaked:
            raise ProtocolError(
                'handshake must be called only once '
                'before any other messages are send to remote peer',
            )

        self.send(handshake)

        tries = 0
        handshake_message = b''

        while (
            len(handshake_message) < messages.Handshake.message_length
            and tries < 10
        ):
            handshake_message = self.conn.recv(
                messages.Handshake.message_length,
            )
            tries += 1

        raw_message = RawPeerMessage.from_bytes(handshake_message)
        peer_handshake = messages.Handshake.decode_from_raw(raw_message)

        if peer_handshake.info_hash != handshake.info_hash:
            raise ProtocolError('Remote peer report other info hash')

        self.handshaked = True

        return peer_handshake

    def receive(self) -> BasePeerMessage:
        """Receive message from remote peer."""
        if not self.handshaked:
            raise ProtocolError(
                'handshake must be called before send or'
                ' receive any other messages from remote peer',
            )

        tries = 0
        message_length_bytes = b''

        while len(message_length_bytes) < 4 and tries < 10:
            message_length_bytes = self.conn.recv(4)
            tries += 1

        if len(message_length_bytes) != 4:
            raise ProtocolError(
                'unable to read message length from remote peer',
            )

        try:
            message_length, *_ = struct.unpack('>I', message_length_bytes)
        except struct.error as err:
            raise ProtocolError(
                'cannot unpack message length from bytes to integer',
            ) from err

        message_body = b''

        while len(message_body) < message_length:
            received = self.conn.recv(message_length - len(message_body))
            message_body += received

        raw_message_bytes = message_length_bytes + message_body
        raw_message = RawPeerMessage.from_bytes(raw_message_bytes)

        peer_message = MESSAGES[raw_message.message_id].decode_from_raw(
            # NOTE: mypy misunderstood this call of a classmethod
            raw_message,  # type: ignore
        )

        return peer_message

    def send(self, message: BasePeerMessage):
        """Send message to remote peer."""
        self.conn.sendall(message.encode())

    def __enter__(self) -> 'P2PConnection':
        """Context manager for peer to peer connection."""
        self.conn.connect((str(self.peer.ip), self.peer.port))
        return self

    def __exit__(self, err_type, err_value, traceback):
        """Exit from context closes any connections."""
        self.conn.close()
