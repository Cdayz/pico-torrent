"""Console application of pico-torrent."""

import sys
import argparse
import dataclasses

from typing import List
from pathlib import Path

from pico_torrent.protocol.metainfo.torrent import TorrentFile
from pico_torrent.protocol.trackers.tracker import TorrentTracker
from pico_torrent.protocol.peers import connection, messages
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


def run():
    """Enter function of cli application."""
    options = parse_cmd_args(sys.argv[1:])

    with options.torrent_file.open('rb') as f:
        torrent = TorrentFile.from_torrent_file(f)

        # ========================================================
        # NOTE: if we work in peer serve mode
        # ========================================================
        # server = TorrentServer(torrent, output_file_or_folder)
        # server.serve_torrent()
        # ========================================================
        # NOTE: if we work in download mode
        # ========================================================
        # client = TorrentClient(torrent)
        # client.download()
        # ========================================================
        # NOTE: all of below must be inside TorrentClient class
        # NOTE: trackers manager works with multiply trackers
        # NOTE: to return peers into peers manager
        # tracker = TorrentTrackersManager(torrent)
        # NOTE: peers manager saves connections to peers and download pieces
        # NOTE: and peers manager mark peers as bad and not work with it
        # peers = PeersManager(tracker)

        peer_id = peer_utils.generate_peer_id()

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

        with connection.P2PConnection(first_peer) as conn:
            handshake_msg = messages.Handshake(
                torrent.info_hash,
                tracker.this_peer_id.encode(),
            )
            remote_handshake = conn.handshake(handshake_msg)

            print(f'Received {remote_handshake}')
