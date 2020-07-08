"""Torrent file definitions."""

import hashlib
import datetime
import dataclasses

from pathlib import Path
from typing import Optional, BinaryIO, List

from pico_torrent import bencode


class BadTorrentFile(Exception):
    """Exception when cannot parse given file into TorrentFile."""


@dataclasses.dataclass
class TorrentInfoFile:
    """Torrent file info."""

    path: Path
    length: int


@dataclasses.dataclass
class TorrentInfo:
    """Torrent information."""

    name: str
    pieces: List[bytes]
    piece_length: int
    files: List[TorrentInfoFile]


@dataclasses.dataclass
class TorrentFile:
    """Torrent file definition."""

    announce: str

    announce_list: Optional[List[str]]

    comment: Optional[str]
    created_by: Optional[str]
    creation_date: Optional[datetime.datetime]

    info: TorrentInfo
    info_hash: bytes

    @staticmethod
    def from_torrent_file(bencode_file: BinaryIO) -> 'TorrentFile':
        """Convert given file-like object to TorrentFile object."""
        try:
            decoder = bencode.BencodeDecoder(bencode_file)
            data = decoder.decode()
        except bencode.BencodeDecodeError:
            raise BadTorrentFile("It's not a torrent file")

        if not isinstance(data, dict):
            raise BadTorrentFile("It's not a torrent file")

        info = data[b'info']
        info_bytes = bencode.BencodeEncoder().encode(info).getvalue()
        info_hash = hashlib.sha1(info_bytes).digest()  # noqa: S303

        torrent_files = []

        if b'files' in data[b'info']:
            for f_dict in data[b'info'][b'files']:
                torrent_files.append(TorrentInfoFile(
                    path=Path(
                        '/'.join(item.decode() for item in f_dict[b'path']),
                    ),
                    length=f_dict[b'length'],
                ))

        else:
            torrent_files.append(TorrentInfoFile(
                path=Path(data[b'info'][b'name'].decode()),
                length=data[b'info'][b'length'],
            ))

        pieces = []
        pieces_bytes = [
            data[b'info'][b'pieces'][index:index+1]
            for index in range(len(data[b'info'][b'pieces']))
        ]

        piece = b''
        for index, symbol in enumerate(pieces_bytes):
            piece += symbol

            if index != 0 and index % 20 == 0:
                pieces.append(piece)
                piece = b''

        if piece:
            pieces.append(piece)

        info = TorrentInfo(
            name=data[b'info'][b'name'].decode(),
            pieces=pieces,
            piece_length=data[b'info'][b'piece length'],
            files=torrent_files,
        )

        announce_list = []
        if b'announce-list' in data:
            for item in data[b'announce-list']:
                announce_list.append(item[0].decode())

        comment = data.get(b'comment', b'')
        created_by = data.get(b'created by', b'')
        creation_date = data.get(b'creation date')

        if creation_date:
            creation_date = datetime.datetime.fromtimestamp(creation_date)

        definition = TorrentFile(
            announce=data[b'announce'].decode(),
            announce_list=announce_list or None,
            comment=comment.decode() or None,
            created_by=created_by.decode() or None,
            creation_date=creation_date or None,
            info=info,
            info_hash=info_hash,
        )

        return definition
