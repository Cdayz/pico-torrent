"""Console application of pico-torrent."""

import sys
import argparse
import dataclasses

from typing import List
from pathlib import Path

from pico_torrent.torrent import TorrentFile
from pico_torrent.tracker import TorrentTracker


@dataclasses.dataclass
class CmdOptions:
    """Command line options."""

    torrent_file: Path


def parse_cmd_args(args: List[str]) -> CmdOptions:
    """Parse command line arguments into CmdOptions object."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--torrent-file',
        help='Path to torrent file',
        action='store',
        type=Path,
        required=True,
    )

    ns = parser.parse_args(args)

    return CmdOptions(
        torrent_file=ns.torrent_file,
    )


def run():
    """Enter function of cli application."""
    options = parse_cmd_args(sys.argv[1:])

    with options.torrent_file.open('rb') as f:
        torrent = TorrentFile.from_torrent_file(f)
        tracker = TorrentTracker(
            torrent_announce_url=torrent.announce,
            torrent_info_hash=torrent.info_hash,
            full_torrent_bytes=(
                len(torrent.info.pieces)*torrent.info.piece_length
            ),
        )

        peers = tracker.get_available_peers()
        print(peers)