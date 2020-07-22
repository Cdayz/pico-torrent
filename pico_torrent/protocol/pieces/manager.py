"""Pieces manager."""

from typing import Dict

from pico_torrent.protocol.peers.peer import TorrentPeer
from pico_torrent.protocol.peers.messages import BitField, Have, Piece
from pico_torrent.protocol.metainfo.torrent import TorrentFile


PieceIndex = int
Exists = bool


class PieceLookup:
    """Pieces lookup from bit field."""

    def __init__(self):
        """Initialize pieces lookup."""
        self.lookup: Dict[PieceIndex, Exists] = {}

    def add_by_have_message(self, have: Have):
        """Add piece existence by have message."""
        self.lookup[have.piece_index] = True

    def add_by_bitfield_message(self, bitfield: BitField):
        """Add piece existence by bitfield message."""
        for piece_index, piece_exists in enumerate(bitfield.bit_field_lookup):
            self.lookup[piece_index] = (
                self.lookup.get(piece_index) or piece_exists
            )


class PiecesManager:
    """Pieces manager."""

    def __init__(self, torrent: TorrentFile):
        """Initialize pieces manager."""
        self.torrent = torrent
        self.peers: Dict[TorrentPeer, PieceLookup] = {}

    def add_peer_with_bitfield(self, peer: TorrentPeer, bitfield: BitField):
        """Add peed pieces blocks by remote peer bitfield message."""
        lookup: PieceLookup = self.peers.get(peer, PieceLookup())
        lookup.add_by_bitfield_message(bitfield)

        self.peers[peer] = lookup

    def add_peer_with_have_message(self, peer: TorrentPeer, have: Have):
        """Add peer piece blocks by remote peer have message."""
        lookup: PieceLookup = self.peers.get(peer, PieceLookup())
        lookup.add_by_have_message(have)

        self.peers[peer] = lookup

    def remove_peer(self, peer: TorrentPeer):
        """Remove given peer from peers lookup."""
        self.peers.pop(peer, None)

    def add_piece(self, piece: Piece):
        """Add fetched piece to fetched pieces."""
