"""Peers related utilities."""

import random

from pico_torrent import __version__


def generate_peer_id() -> str:
    """Generate peer id."""
    prefix = '-PC' + __version__.replace('.', '') + '0-'
    peer_number = ''.join(
        str(random.randint(0, 9)) for _ in range(12)  # noqa: S311
    )

    return f'{prefix}{peer_number}'
