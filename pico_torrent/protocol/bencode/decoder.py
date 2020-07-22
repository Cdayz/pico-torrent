"""Bencode decoder."""

import collections

from typing import Union, BinaryIO

BencodeValue = Union[list, dict, int, bytes]


class BencodeDecodeError(Exception):
    """Exception when cannot parse bencode file."""


class BencodeDecoder:
    """Decoder for BENCODE format."""

    def __init__(self, bencode_file: BinaryIO):
        """Initialize bencode decoder."""
        self._bencode_file = bencode_file

        self._decode_func = {
            b'i': self._decode_int,
            b'l': self._decode_list,
            b'd': self._decode_dict,
            # Bytes read hack
            b'0': self._decode_bytes,
            b'1': self._decode_bytes,
            b'2': self._decode_bytes,
            b'3': self._decode_bytes,
            b'4': self._decode_bytes,
            b'5': self._decode_bytes,
            b'6': self._decode_bytes,
            b'7': self._decode_bytes,
            b'8': self._decode_bytes,
            b'9': self._decode_bytes,
        }

    def decode(self) -> BencodeValue:
        """Decode bencoded sequence into python object."""
        dtype = self._bencode_file.read(1)

        try:
            return self._decode_func[dtype](dtype)
        except (KeyError, ValueError, TypeError):
            raise BencodeDecodeError("not a valid bencoded file")

    def _read_until(self, sep: bytes) -> bytes:
        """Read bytes from file while not reached separator."""
        if len(sep) != 1:
            raise ValueError("length of separator must be 1")

        readed_byte = self._bencode_file.read(1)
        readed_bytes = b''

        while readed_byte != sep:
            readed_bytes += readed_byte
            readed_byte = self._bencode_file.read(1)

        return readed_bytes

    def _decode_int(self, dtype: bytes):
        """Decode integer value."""
        int_bytes = self._read_until(b'e')
        return int(int_bytes, base=10)

    def _decode_bytes(self, dtype: bytes) -> bytes:
        """Decode bytes value."""
        length = int(dtype + self._read_until(b':'))
        content = self._bencode_file.read(length)

        return content

    def _decode_list(self, dtype: bytes) -> list:
        """Decode list of items."""
        lst = []
        dtype = self._bencode_file.read(1)

        while dtype != b'e':
            lst.append(self._decode_func[dtype](dtype))
            dtype = self._bencode_file.read(1)

        return lst

    def _decode_dict(self, dtype: bytes) -> dict:
        """Decode dictionary."""
        dct = collections.OrderedDict()
        dtype = self._bencode_file.read(1)

        while dtype != b'e':
            key = self._decode_func[dtype](dtype)
            dtype = self._bencode_file.read(1)
            value = self._decode_func[dtype](dtype)
            dct[key] = value

            dtype = self._bencode_file.read(1)

        return dct
