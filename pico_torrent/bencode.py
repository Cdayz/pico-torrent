"""Bencode data encoding encoder and decoder."""

import io

from typing import BinaryIO, Union
from collections import OrderedDict

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
        dct = OrderedDict()
        dtype = self._bencode_file.read(1)

        while dtype != b'e':
            key = self._decode_func[dtype](dtype)
            dtype = self._bencode_file.read(1)
            value = self._decode_func[dtype](dtype)
            dct[key] = value

            dtype = self._bencode_file.read(1)

        return dct


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
            OrderedDict: self._encode_dict,
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
