"""Abstract class for P2P messages."""

import abc

from pico_torrent.protocol.peers.raw_message import (
    RawPeerMessage,
    PeerMessageId,
)


class BasePeerMessage(abc.ABC):
    """Abstract class for peer messages.

    That is message between two peers.
    """

    @property
    @abc.abstractmethod
    def message_id(self) -> PeerMessageId:
        """Peer Message Id."""

    @abc.abstractclassmethod
    def decode_from_raw(cls, raw_message: RawPeerMessage):
        """Decode into class from raw peer messsage."""

    @abc.abstractmethod
    def encode(self) -> bytes:
        """Encode message to bytes."""

    @classmethod
    def _check_message_type(cls, raw: RawPeerMessage):
        if cls.message_id != raw.message_id:
            raise ValueError(
                'Cannot convert raw_message with '
                'type {0} to message with type {1}'
                .format(
                    cls.message_id.name,  # type: ignore
                    raw.message_id.name,
                ),
            )
