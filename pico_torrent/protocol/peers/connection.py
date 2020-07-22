"""Peer-to-Peer connection protocol."""

import socket
import struct
import logging

from typing import Type, Dict, List


from pico_torrent.protocol.peers import messages
from pico_torrent.protocol.peers.peer import TorrentPeer
from pico_torrent.protocol.peers.abstract import BasePeerMessage
from pico_torrent.protocol.peers.raw_message import (
    PeerMessageId,
    RawPeerMessage,
)
from pico_torrent.protocol.pieces.manager import PiecesManager

from pico_torrent.protocol.metainfo.torrent import TorrentFile

logger = logging.getLogger('pico_torrent.protocol.peers.connection')


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

    def __init__(self, peer: TorrentPeer):
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

    def connect(self):
        """Connect to remote peer."""
        self.conn.connect((str(self.peer.ip), self.peer.port))

    def disconnect(self):
        """Disconnect from remote peer."""
        self.conn.close()

    def __enter__(self) -> 'P2PConnection':
        """Context manager for peer to peer connection."""
        self.connect()
        return self

    def __exit__(self, err_type, err_value, traceback):
        """Exit from context closes any connections."""
        self.disconnect()


class P2PReadMessageStream:
    """Peer to peer message stream."""

    def __init__(self, conn: P2PConnection):
        """Initialize message stream."""
        if not conn.handshaked:
            raise ValueError('only handshaked connections can be readed')

        self.connection = conn

    def __iter__(self) -> 'P2PReadMessageStream':
        """Return iterator of message stream."""
        return self

    def __next__(self) -> BasePeerMessage:
        """Return next peer message from stream."""
        try:
            return self.connection.receive()

        except ConnectionError:
            raise StopIteration()

        except Exception as err:
            logger.exception(err)
            raise StopIteration()


class TorrentPeerConnection:
    """Peer to peer connection by BitTorrent protocol."""

    def __init__(
        self,
        remote_peer: TorrentPeer,
        torrent: TorrentFile,
        peer_id: str,
        pieces_manager: PiecesManager,
    ):
        """Initialize connection."""
        self.remote_peer = remote_peer
        self.connection = P2PConnection(self.remote_peer)
        self.torrent = torrent
        self.this_peer_id = peer_id
        self.pieces_manager = pieces_manager
        # States of peers
        self.this_peer_state: List[str] = []
        self.remote_peer_state: List[str] = []

    def cancel(self):
        """Cancel working with that peer."""
        logger.info(f'Disconnect from peer {self.remote_peer.ip}')
        self.pieces_manager.remove_peer(self.remote_peer)
        self.connection.disconnect()

    def communicate(self):
        """Communicate with remote peer by BitTorrent protocol."""
        try:
            self._communicate()
        except ProtocolError as err:
            logger.exception('Protocol error')
            logger.exception(err)
        except (ConnectionRefusedError, TimeoutError) as err:
            logger.exception('Connection was refused or a timeout was reached')
            logger.exception(err)
        except ConnectionResetError as err:
            logger.exception('Connection to remote peer was reset')
            logger.exception(err)

        self.cancel()

    def _request_piece(self):
        # TODO: implement request of piece
        pass

    def _piece_given(self, piece_message: messages.Piece):
        self.pieces_manager.add_piece(piece_message)

    def _bitfield_given(self, bitfield_message: messages.BitField):
        self.pieces_manager.add_peer_with_bitfield(
            self.remote_peer,
            bitfield_message,
        )

    def _have_given(self, have_message: messages.Have):
        self.pieces_manager.add_peer_with_have_message(
            self.remote_peer,
            have_message,
        )

    def _communicate(self):
        """Communicate with remote peer by BitTorrent protocol."""
        logger.info(f'Try to connect with peer {self.remote_peer.ip}')
        self.connection.connect()
        logger.info(f'Connected to peer {self.remote_peer.ip}')

        logger.info(f'Handshake with peer {self.remote_peer.ip}')
        self.connection.handshake(
            messages.Handshake(
                info_hash=self.torrent.info_hash,
                peer_id=self.this_peer_id.encode(),
            ),
        )
        logger.info(f'Success handshaked with peer {self.remote_peer.ip}')

        self.this_peer_state.append('choked')
        logger.info(f'Send `interested` message to peer {self.remote_peer.ip}')
        self.connection.send(messages.Interested())

        self.this_peer_state.append('interested')

        for message in P2PReadMessageStream(self.connection):
            if message.message_id == PeerMessageId.Interested:
                logger.info(
                    f'Got `interested` message '
                    f'from peer {self.remote_peer.ip}',
                )
                if 'not interested' in self.remote_peer_state:
                    self.remote_peer_state.remove('not interested')

                self.remote_peer_state.append('interested')

            elif message.message_id == PeerMessageId.NotInterested:
                logger.info(
                    f'Got `not interested` message '
                    f'from peer {self.remote_peer.ip}',
                )
                if 'interested' in self.remote_peer_state:
                    self.remote_peer_state.remove('interested')

                self.remote_peer_state.append('not interested')

            elif message.message_id == PeerMessageId.Choke:
                logger.info(
                    f'Got `choke` message from peer {self.remote_peer.ip}',
                )
                if 'unchoked' in self.this_peer_state:
                    self.this_peer_state.remove('unchoked')

                self.this_peer_state.append('choked')

            elif message.message_id == PeerMessageId.Unchoke:
                logger.info(
                    f'Got `unchoke` message from peer {self.remote_peer.ip}',
                )
                if 'choked' in self.this_peer_state:
                    self.this_peer_state.remove('choked')

                self.this_peer_state.append('unchoked')

            elif message.message_id == PeerMessageId.Request:
                logger.info(
                    f'Ignore `request` message '
                    f'from peer {self.remote_peer.ip}',
                )

            elif message.message_id == PeerMessageId.Cancel:
                logger.info(
                    f'Ignore `cancel` message '
                    f'from peer {self.remote_peer.ip}',
                )

            elif message.message_id == PeerMessageId.KeepAlive:
                logger.info(
                    f'Ignore `keep-alive` message '
                    f'from peer {self.remote_peer.ip}',
                )

            elif message.message_id == PeerMessageId.Have:
                logger.info(
                    f'Got `have` message '
                    f'from remote peer {self.remote_peer.ip}',
                )
                self._have_given(message)

            elif message.message_id == PeerMessageId.BitField:
                logger.info(
                    f'Got `bitfield` message '
                    f'from remote peer {self.remote_peer.ip}',
                )
                self._bitfield_given(message)

            elif message.message_id == PeerMessageId.Piece:
                logger.info(
                    f'Got `piece` message '
                    f'from remote peer {self.remote_peer.ip}',
                )
                self._piece_given(message)

            if 'choked' not in self.this_peer_state:
                if 'interested' in self.this_peer_state:
                    if 'pending request' not in self.this_peer_state:
                        self.this_peer_state.append('pending request')
                        logger.info(
                            f'Pending request piece '
                            f'from peer {self.remote_peer.ip}',
                        )
                        self._request_piece()
