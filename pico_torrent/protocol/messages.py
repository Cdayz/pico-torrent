"""Messages of P2P protocol."""

import struct

from .abstract import BasePeerMessage
from .raw_message import RawPeerMessage, PeerMessageId


class Handshake(BasePeerMessage):
    """Handshake message of P2P protocol.

    format: <pstrlen><pstr><reserved><info_hash><peer_id>

    where:
        pstrlen - string length of <pstr>, as a single raw byte
        pstr - string identifier of the protocol, 'BitTorrent protocol'
        reserved - 8 reserved bytes, padding
        info_hash - 20-bytes SHA1 hash of info key of torrent file
        peer_id - 20-bytes string used as ID of peer
    """

    message_id = PeerMessageId.Handshake

    def __init__(self, info_hash: bytes, peer_id: bytes):
        """Initialize Handshake message."""
        self.peer_id = peer_id
        self.info_hash = info_hash

    @classmethod
    def decode_from_raw(cls, raw_message: RawPeerMessage):
        """Decode handshake from raw message."""
        cls._check_message_type(raw_message)
        parts = struct.unpack('>B19s8x20s20s', raw_message.payload)

        return cls(info_hash=parts[2], peer_id=parts[3])

    def encode(self) -> bytes:
        """Encode message to bytes."""
        return struct.pack(
            '>B19s8x20s20s',
            19,                         # Single byte (B)
            b'BitTorrent protocol',     # String 19s
                                        # Reserved 8x (pad byte, no value)
            self.info_hash,             # String 20s
            self.peer_id,               # String 20s
        )


class KeepAlive(BasePeerMessage):
    """KeepAlive message of P2P protocol.

    format: <len=0000>

    This message has no any payload.
    """

    message_id = PeerMessageId.KeepAlive

    @classmethod
    def decode_from_raw(cls, raw_message: RawPeerMessage):
        """Decode from raw peer message."""
        cls._check_message_type(raw_message)
        return cls()

    def encode(self) -> bytes:
        """Encode message to bytes."""
        return struct.pack('>I', 0)


class Choke(BasePeerMessage):
    """Choke message of P2P protocol.

    format: <len=0001><id=0>

    This method indicates that connected client are choked from now.
    """

    message_id = PeerMessageId.Choke

    @classmethod
    def decode_from_raw(cls, raw_message: RawPeerMessage):
        """Decode from raw peer message."""
        cls._check_message_type(raw_message)
        return cls()

    def encode(self) -> bytes:
        """Encode message to bytes."""
        return struct.pack('>Ib', 1, 0)


class Unchoke(BasePeerMessage):
    """Unchoke message of P2P protocol.

    format: <len=0001><id=1>

    This message indicates that connected client are unchoked from now.
    """

    message_id = PeerMessageId.Unchoke

    @classmethod
    def decode_from_raw(cls, raw_message: RawPeerMessage):
        """Decode from raw peer message."""
        cls._check_message_type(raw_message)
        return cls()

    def encode(self) -> bytes:
        """Encode message to bytes."""
        return struct.pack('>Ib', 1, 1)
