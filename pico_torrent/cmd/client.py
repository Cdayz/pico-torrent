"""Console application of pico-torrent."""

import sys
import logging
import argparse
import dataclasses

from typing import List
from pathlib import Path

from pico_torrent.protocol.metainfo.torrent import TorrentFile
from pico_torrent.protocol.trackers.tracker import TorrentTracker
from pico_torrent.protocol.peers import connection
from pico_torrent.protocol.utils import peers as peer_utils


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


def init_logging() -> logging.Logger:
    """Initialize logger."""
    logger = logging.getLogger('pico_torrent')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    handler.setFormatter(formatter)
    logger.propagate = False
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


def run():
    """Enter function of cli application."""
    logger = init_logging()

    options = parse_cmd_args(sys.argv[1:])

    with options.torrent_file.open('rb') as f:
        logger.info(f'Selected metainfo file {options.torrent_file}')
        torrent = TorrentFile.from_torrent_file(f)
        logger.info('Metainfo file successfully parsed')

        peer_id = peer_utils.generate_peer_id()
        logger.info(f'Generated peer id is {peer_id!r}')

        tracker = TorrentTracker(
            torrent_announce_url=torrent.announce,
            torrent_info_hash=torrent.info_hash,
            full_torrent_bytes=(
                len(torrent.info.pieces)*torrent.info.piece_length
            ),
            this_peer_id=peer_id,
            this_peer_listen_port=6889,
        )

        peers = tracker.get_available_peers()
        first_peer = peers[0]

        pieces_manager = connection.PiecesManager(torrent)

        conn = connection.TorrentPeerConnection(
            remote_peer=first_peer,
            torrent=torrent,
            peer_id=peer_id,
            pieces_manager=pieces_manager,
        )

        conn.communicate()
