import io
import collections

from typing import Union

BencodeValue = Union[list, dict, int, bytes]


class BencodeEncodeError(Exception):
    """Exception when cannot generate bencode bytes from given value."""


class BencodeEncoder:
    """Encoder for BENCODE format."""

    def __init__(self):
        """Initialize encoder."""
        self._buffer = io.BytesIO()
        self._encode_func = {
            int: self._encode_int,
            bytes: self._encode_bytes,
            list: self._encode_list,
            dict: self._encode_dict,
            collections.OrderedDict: self._encode_dict,
        }

    def encode(self, value: BencodeValue) -> io.BytesIO:
        """Encode given value into bencode."""
        try:
            self._encode_func[type(value)](value)
        except (KeyError, ValueError, TypeError):
            raise BencodeEncodeError("Not a valid object for bencoding")

        self._buffer.seek(0)
        return self._buffer

    def _encode_int(self, value: int):
        """Encode integer value."""
        self._buffer.write(b'i')
        self._buffer.write(str(value).encode())
        self._buffer.write(b'e')

    def _encode_bytes(self, value: bytes):
        """Encode bytes value."""
        length = len(value)
        self._buffer.write(str(length).encode())
        self._buffer.write(b':')
        self._buffer.write(value)

    def _encode_list(self, value: list):
        """Encode list value."""
        self._buffer.write(b'l')
        for item in value:
            self._encode_func[type(item)](item)
        self._buffer.write(b'e')

    def _encode_dict(self, value: dict):
        """Encode dictionary value."""
        self._buffer.write(b'd')
        for k, v in value.items():
            self._encode_func[type(k)](k)
            self._encode_func[type(v)](v)
        self._buffer.write(b'e')
