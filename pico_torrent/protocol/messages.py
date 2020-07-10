"""Messages of P2P protocol."""

import struct

from typing import List

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
        return struct.pack('>Ib', 1, self.message_id)


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
        return struct.pack('>Ib', 1, self.message_id)


class Interested(BasePeerMessage):
    """Interested message of P2P protocol.

    format: <len=0001><id=2>

    This message indicates that connected client interested to download pieces.
    """

    message_id = PeerMessageId.Interested

    @classmethod
    def decode_from_raw(cls, raw_message: RawPeerMessage):
        """Decode from raw peer message."""
        cls._check_message_type(raw_message)
        return cls()

    def encode(self) -> bytes:
        """Encode message to bytes."""
        return struct.pack('>Ib', 1, self.message_id)


class NotInterested(BasePeerMessage):
    """NotInterested message of P2P protocol.

    format: <len=0001><id=3>

    This message indicates that connected client not interested to load pieces.
    """

    message_id = PeerMessageId.NotInterested

    @classmethod
    def decode_from_raw(cls, raw_message: RawPeerMessage):
        """Decode from raw peer message."""
        cls._check_message_type(raw_message)
        return cls()

    def encode(self) -> bytes:
        """Encode message to bytes."""
        return struct.pack('>Ib', 1, self.message_id)


class Have(BasePeerMessage):
    """Have message of P2P protocol.

    format: <len=0005><id=4><piece index>

    This message indicates that peer have such piece of data by <piece index>.
    """

    message_id = PeerMessageId.Have

    def __init__(self, piece_index: int):
        """Initialize Have message with haved piece index."""
        self.piece_index = piece_index

    @classmethod
    def decode_from_raw(cls, raw_message: RawPeerMessage):
        """Decode from raw peer message."""
        cls._check_message_type(raw_message)
        piece_index, *_ = struct.unpack('>I', raw_message.payload)
        return cls(piece_index=piece_index)

    def encode(self) -> bytes:
        """Encode message to bytes."""
        return struct.pack('>IbI', 5, self.message_id, self.piece_index)


class BitField(BasePeerMessage):
    """BitField message of P2P protocol.

    format: <len=0001+X><id=5><bitfield>

    X - is length of bit field

    This message indicates bitfield length of all pieces of torrent.
    If bit of bitfield of index i is 0 - then peer does not have such piece.
    If bit of bitfield of index i is 1 - then peer have such piece of data.
    """

    message_id = PeerMessageId.BitField

    def __init__(self, raw_bitfield: bytes):
        """Initialize bit field message."""
        self.raw_bitfield = raw_bitfield
        self.bit_field_lookup: List[bool] = []

        # FIXME: it's a dirty hack, maybe any other ways of conversion exists?
        BYTE_LENGTH = 8  # bit
        for byte in self.raw_bitfield:
            bin_representation = bin(byte)[2:]
            bits = [False] * BYTE_LENGTH
            start_index = BYTE_LENGTH - len(bin_representation)

            for index, symbol in enumerate(bin_representation):
                bits[start_index + index] = symbol == '1'

            self.bit_field_lookup.extend(bits)

    def have_piece(self, piece_index: int) -> bool:
        """Check that bitfield have piece by piece index."""
        if piece_index > len(self.bit_field_lookup):
            raise ValueError(
                f'piece index {piece_index} greater than bit field',
            )

        return self.bit_field_lookup[piece_index]

    @classmethod
    def decode_from_raw(cls, raw_message: RawPeerMessage):
        """Decode from raw peer message."""
        cls._check_message_type(raw_message)
        bitfield, *_ = struct.unpack(
            f'>{raw_message.length - 1}s',
            raw_message.payload,
        )
        return cls(raw_bitfield=bitfield)

    def encode(self) -> bytes:
        """Encode message to bytes."""
        return struct.pack(
            f'>Ib{len(self.raw_bitfield)}s',
            len(self.raw_bitfield)+1,
            self.message_id,
            self.raw_bitfield,
        )
