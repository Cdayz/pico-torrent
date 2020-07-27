"""Map pieces to files."""

import dataclasses

from typing import List
from pathlib import Path

from .torrent import TorrentInfoFile


@dataclasses.dataclass
class PieceSlice:
    """Piece slice to file."""

    piece_index: int
    offset: int
    length: int


@dataclasses.dataclass
class MappedToPiecesFile:
    """File mapped to piece slices."""

    path: Path
    length: int
    pieces: List[PieceSlice]


def map_files_to_pieces(
    files: List[TorrentInfoFile],
    pieces_count: int,
    piece_length: int,
) -> List[MappedToPiecesFile]:
    """Map pieces to torrent files."""
    _files = [file.length for file in files]
    pieces_to_files_mapping: List[List[PieceSlice]] = []

    current_piece_index = 0
    current_piece_offset = 0

    while _files:
        pieces_to_files_mapping.append([])
        current_file_size, _files = _files[0], _files[1:]

        while current_file_size > 0:
            current_piece_length = piece_length - current_piece_offset

            if current_file_size < current_piece_length:
                pieces_to_files_mapping[-1].append(PieceSlice(
                    piece_index=current_piece_index,
                    offset=current_piece_offset,
                    length=current_piece_offset+current_file_size,
                ))
                current_piece_offset += current_file_size
                current_file_size = 0

            else:
                pieces_to_files_mapping[-1].append(PieceSlice(
                    piece_index=current_piece_index,
                    offset=current_piece_offset,
                    length=piece_length,
                ))
                current_piece_index += 1
                current_piece_offset = 0
                current_file_size -= current_piece_length

    return [
        MappedToPiecesFile(
            path=file.path,
            length=file.length,
            pieces=pieces,
        )
        for file, pieces in zip(files, pieces_to_files_mapping)
    ]
