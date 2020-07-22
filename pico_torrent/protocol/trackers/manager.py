"""Trackers manager."""

import datetime

from typing import List, Tuple, Optional

from pico_torrent.protocol.peers.peer import TorrentPeer
from pico_torrent.protocol.trackers.tracker import (
    TorrentTracker,
    BadTrackerResponse,
)


TrackerWithLastVisitDate = Tuple[TorrentTracker, Optional[datetime.datetime]]


class TrackersManager:
    """Torrent trackers manager."""

    def __init__(self, trackers: List[TorrentTracker]):
        """Initialize trackers manager."""
        self.trackers: List[TrackerWithLastVisitDate] = [
            (tracker, None)
            for tracker in trackers
        ]

    def get_remote_peers(self) -> List[TorrentPeer]:
        """Fetch all avaliable remote peers."""
        now = datetime.datetime.now()

        all_avaliable_peers: List[TorrentPeer] = []

        for index, (tracker, last_visited) in enumerate(self.trackers):
            if last_visited is not None:
                time_to_next_visit = (
                    last_visited
                    + datetime.timedelta(seconds=(tracker.interval or 0))
                )
                if time_to_next_visit >= now:
                    continue

            try:
                available_peers_from_tracker = tracker.get_available_peers()
            except BadTrackerResponse:
                continue

            available_peers_from_tracker.extend(available_peers_from_tracker)

            # Update last visit time
            self.trackers[index] = (tracker, now)

        return all_avaliable_peers
