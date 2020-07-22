"""Raw message of P2P protocol."""

import enum
import struct
import dataclasses


class PeerMessageId(enum.IntEnum):
    """Peer message ids according to specification."""

    Choke = 0
    Unchoke = 1
    Interested = 2
    NotInterested = 3
    Have = 4
    BitField = 5
    Request = 6
    Piece = 7
    Cancel = 8
    Port = 9

    # Message Ids which not in specification
    KeepAlive = -1  # KeepAlive does not have id according to specification
    Handshake = -2  # Handshake is not real message


@dataclasses.dataclass
class RawPeerMessage:
    """Raw peer message."""

    length: int
    message_id: PeerMessageId
    payload: bytes

    @staticmethod
    def from_bytes(raw_payload: bytes) -> 'RawPeerMessage':
        """Convert raw bytes payload into RawPeerMessage."""
        # Check for Handshake message
        try:
            parts = struct.unpack('>B19s8x20s20s', raw_payload)
        except struct.error:
            pass
        else:
            if parts[1] == b'BitTorrent protocol':
                return RawPeerMessage(
                    length=19,
                    message_id=PeerMessageId.Handshake,
                    payload=raw_payload,
                )

        length, *_ = struct.unpack('>I', raw_payload[:4])

        # Check for KeepAlive message
        if length == 0:
            return RawPeerMessage(
                length=0,
                message_id=PeerMessageId.KeepAlive,
                payload=b'',
            )

        message_id, *_ = struct.unpack('>B', raw_payload[4:5])

        return RawPeerMessage(
            length=length,
            message_id=PeerMessageId(message_id),
            payload=raw_payload[5:5+length],
        )
