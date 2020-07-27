"""Piece definitions."""

import enum
import hashlib
import dataclasses

from typing import List, Optional


class BlockStatus(enum.Enum):
    """Piece block status."""

    Missing = 0
    Pending = 1
    Retreived = 2


@dataclasses.dataclass
class PieceBlock:
    """Piece block.

    Block is a part of whole piece that is transfered between peers.
    Last might be smaller than a standart request size.
    """

    piece_index: int
    offset: int
    length: int

    data: bytes = b''
    status: BlockStatus = BlockStatus.Missing


class Piece:
    """Piece is part of torrent data wich constructs from piece blocks."""

    def __init__(self, index: int, piece_hash: str, blocks: List[PieceBlock]):
        """Initialize piece."""
        self.index = index
        self.hash = piece_hash
        self.blocks = {
            block.offset: block
            for block in blocks
        }

    def next_block_for_request(self) -> Optional[PieceBlock]:
        """Return next block for request it from remote peer."""
        for offset in self.blocks:
            block = self.blocks[offset]

            if block.status == BlockStatus.Missing:
                self.blocks[offset].status = BlockStatus.Pending
                return block

        return None

    def reset(self):
        """Set all piece blocks to missing state."""
        for offset in self.blocks:
            self.blocks[offset].status = BlockStatus.Missing
            self.blocks[offset].data = b''

    def add_block(self, offset: int, data: bytes):
        """Add block to piece."""
        if offset not in self.blocks:
            # TODO: warn in logs
            return

        self.blocks[offset].status = BlockStatus.Retreived
        self.blocks[offset].data = data

    def is_complete(self) -> bool:
        """Check that piece is fully complete."""
        return all(
            block.status == BlockStatus.Retreived
            for block in self.blocks.values()
        )

    @property
    def content(self) -> bytes:
        """Piece content bytes."""
        return b''.join(
            block.data
            for block in sorted(
                self.blocks.values(),
                key=lambda block: block.offset,
            )
        )

    def is_hash_matching(self) -> bool:
        """Check that content hash match to torrent file hash."""
        content_hash = hashlib.sha1(self.content).digest()  # noqa: S303
        return content_hash == self.hash
