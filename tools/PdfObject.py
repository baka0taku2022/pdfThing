import binascii
import zlib
import struct
import re
from tools.lzw import *


class PdfObject:
    """
    Separate header and object, attempt to decode if encoded
    """
    def __init__(self, raw_object: bytes):
        self.raw_object: bytes = raw_object
        self.object_header: bytes = b''
        self.object_type: bytes = b''
        self.object_body: bytes = b''
        self.obfuscated: bool = False
        self.stream: bytes = b''
        self.filter: bool = False
        self.flate_decode: bool = False
        self.ascii_hex_decode: bool = False
        self.ascii_85_decode: bool = False
        self.run_length_decode: bool = False
        self.lzw_decode: bool = False
        self.jbig2_decode: bool = False
        self.decoded_stream: bytes = b''
        self.ccitt_fax_decode: bool = False
        self.dct_decode: bool = False

    def parse_object(self) -> None:
        self.object_header = self.raw_object[self.raw_object.find(b"<<") + 2: self.raw_object.find(b">>")]
        self.object_body = self.raw_object[self.raw_object.find(b">>") + 2:]
        self.is_obfuscated()
        if self.obfuscated:
            self.object_header = self.deobfuscate(self.object_header)
            self.object_body = self.deobfuscate(self.object_body)


    def parse_header(self) -> None:
        # get object type from header
        if self.object_header.replace(b'\r', b'').replace(b'\n', b'').find(b'/Type') != -1:
            obj_type: bytes = self.object_header.replace(b'\n', b'').replace(b'\r', b'')
            obj_type = obj_type[self.object_header.find(b'/Type') + 5:]
            obj_type = obj_type.strip(b' ')
            obj_type = obj_type[obj_type.find(b'/') + 1:]
            if obj_type[:obj_type.find(b'/') + 1] != b'':
                obj_type = obj_type[:obj_type.find(b'/') + 1]
            obj_type.rstrip()
            self.object_type = obj_type
        else:
            self.object_type = b'N/A'

    def check_filters(self) -> None:
        # check for filters
        if self.object_header.find(b'/Filter') != -1:
            self.filter = True
        # if not then just remove the stream tags if they are there
        else:
            if self.decoded_stream == b'':
                if self.object_body.find(b'stream') != -1:
                    stream = self.object_body[self.object_body.find(b'stream') + 6:]
                    stream = stream[: stream.find(b'endstream')]
                    stream = stream.strip(b'\r\n')
                    self.decoded_stream = stream

    def flate_decode_action(self) -> None:
        self.flate_decode = True
        if self.decoded_stream == b'':
            stream = self.object_body[self.object_body.find(b'stream') + 6:]
            stream = stream[: stream.find(b'endstream')]
            stream = stream.strip(b'\r\n')
        else:
            stream = self.decoded_stream
        try:
            self.decoded_stream: bytes = zlib.decompress(stream)
        except zlib.error as e:
            if e.args[0].find('-3') != -1:  # bad header
                stream = stream[1:]
                self.decoded_stream: bytes = zlib.decompress(stream)
            elif e.args[0].find('-5') != -1:  # truncated data
                print("Flate Decode error: truncated data")
                if self.decoded_stream == b'':
                    stream = self.object_body[self.object_body.find(b'stream') + 6:]
                    stream = stream[: stream.find(b'endstream')]
                    stream = stream.strip(b'\r\n')
                    self.decoded_stream = stream
            else:
                pass
        self.object_type: bytes = b'N/A'

    def ascii_hex_decode_action(self) -> None:
        self.ascii_hex_decode = True
        if self.decoded_stream == b'':
            stream = self.object_body[self.object_body.find(b'stream') + 6:]
            stream = stream[: stream.find(b'endstream')]
            stream = stream.strip(b'\r\n')
        else:
            stream = self.decoded_stream
        try:
            stream = stream.replace(b'>', b'').replace(b' ', b'')
            self.decoded_stream = binascii.unhexlify(stream)
        except binascii.Error:
            print("BinAscii decode error")
            pass

    def ascii_85_decode_action(self) -> None:
        # see LICENSE pdfminer.six this is his code
        # https://github.com/euske/pdfminer/blob/master/pdfminer/ascii85.py
        self.ascii_85_decode = True
        if self.decoded_stream == b'':
            stream = self.object_body[self.object_body.find(b'stream') + 6:]
            stream = stream[: stream.find(b'endstream')]
            stream = stream.strip(b'\r\n')
        else:
            stream = self.decoded_stream
        n = b = 0
        out = b''
        for c in stream:
            if 33 <= c and c <= 117:  # b'!' <= c and c <= b'u'
                n += 1
                b = b * 85 + (c - 33)
                if n == 5:
                    try:
                        out += struct.pack('>L', b)
                    except struct.error:
                        print("Error while ASCII 85 Decoding")
                        pass
                    n = b = 0
            elif c == 122:  # b'z'
                # assert n == 0
                out += b'\0\0\0\0'
            elif c == 126:  # b'~'
                if n:
                    for _ in range(5 - n):
                        b = b * 85 + 84
                    out += struct.pack('>L', b)[:n - 1]
                break
        self.decoded_stream = out

    def run_length_decode_action(self) -> None:
        # see LICENSE pdfminer.six this is his code
        # https://github.com/euske/pdfminer/blob/master/pdfminer/runlength.py
        self.run_length_decode = True
        if self.decoded_stream == b'':
            stream = self.object_body[self.object_body.find(b'stream') + 6:]
            stream = stream[: stream.find(b'endstream')]
            stream = stream.strip(b'\r\n')
        else:
            stream = self.decoded_stream
        decoded = b''
        i = 0
        while i < len(stream):
            # print('data[%d]=:%d:' % (i,ord(data[i])))
            length = stream[i]
            if length == 128:
                break
            if length >= 0 and length < 128:
                run = stream[i + 1:(i + 1) + (length + 1)]
                # print('length=%d, run=%s' % (length+1,run))
                decoded += run
                i = (i + 1) + (length + 1)
            if length > 128:
                run = stream[i + 1:i + 2] * (257 - length)
                # print('length=%d, run=%s' % (257-length,run))
                decoded += run
                i = (i + 1) + 1
        self.decoded_stream = decoded

    def lzw_decode_action(self) -> None:
        self.lzw_decode = True
        if self.decoded_stream == b'':
            stream = self.object_body[self.object_body.find(b'stream') + 6:]
            stream = stream[: stream.find(b'endstream')]
            stream = stream.strip(b'\r\n')
        else:
            stream = self.decoded_stream
        self.decoded_stream = lzwdecode(stream)

    def jbig2_decode_action(self) -> None:
        # Do we need to decode?
        self.jbig2_decode = True
        if self.decoded_stream == b'':
            stream = self.object_body[self.object_body.find(b'stream') + 6:]
            stream = stream[: stream.find(b'endstream')]
            stream = stream.strip(b'\r\n')

    def ccitt_fax_decode_action(self) -> None:
        # Do we need to decode?
        self.ccitt_fax_decode = True
        if self.decoded_stream == b'':
            stream = self.object_body[self.object_body.find(b'stream') + 6:]
            stream = stream[: stream.find(b'endstream')]
            stream = stream.strip(b'\r\n')

    def dct_decode_action(self) -> None:
        self.dct_decode = True
        if self.decoded_stream == b'':
            stream = self.object_body[self.object_body.find(b'stream') + 6:]
            stream = stream[: stream.find(b'endstream')]
            self.decoded_stream = stream.strip(b'\r\n')

    def is_obfuscated(self) -> None:
        regex = b"#[a-fA-F0-9][a-fA-F0-9]"
        chars = re.findall(regex, self.object_header)
        if len(chars) > 0:
            self.obfuscated = True

    def deobfuscate(self, data) -> bytes:
        raw_data = data
        raw_data = raw_data.replace(b"#41", b'A')
        raw_data = raw_data.replace(b"#42", b'B')
        raw_data = raw_data.replace(b"#43", b'C')
        raw_data = raw_data.replace(b"#44", b'D')
        raw_data = raw_data.replace(b"#45", b'E')
        raw_data = raw_data.replace(b"#46", b'F')
        raw_data = raw_data.replace(b"#47", b'G')
        raw_data = raw_data.replace(b"#48", b'H')
        raw_data = raw_data.replace(b"#49", b'I')
        raw_data = raw_data.replace(b"#4a", b'J')
        raw_data = raw_data.replace(b"#4b", b'K')
        raw_data = raw_data.replace(b"#4c", b'L')
        raw_data = raw_data.replace(b"#4d", b'M')
        raw_data = raw_data.replace(b"#4e", b'N')
        raw_data = raw_data.replace(b"#4f", b'O')
        raw_data = raw_data.replace(b"#50", b'P')
        raw_data = raw_data.replace(b"#51", b'Q')
        raw_data = raw_data.replace(b"#52", b'R')
        raw_data = raw_data.replace(b"#53", b'S')
        raw_data = raw_data.replace(b"#54", b'T')
        raw_data = raw_data.replace(b"#55", b'U')
        raw_data = raw_data.replace(b"#56", b'V')
        raw_data = raw_data.replace(b"#57", b'W')
        raw_data = raw_data.replace(b"#58", b'X')
        raw_data = raw_data.replace(b"#59", b'Y')
        raw_data = raw_data.replace(b"#5a", b'Z')
        raw_data = raw_data.replace(b"#61", b'a')
        raw_data = raw_data.replace(b"#62", b'b')
        raw_data = raw_data.replace(b"#63", b'c')
        raw_data = raw_data.replace(b"#64", b'd')
        raw_data = raw_data.replace(b"#65", b'e')
        raw_data = raw_data.replace(b"#66", b'f')
        raw_data = raw_data.replace(b"#67", b'g')
        raw_data = raw_data.replace(b"#68", b'h')
        raw_data = raw_data.replace(b"#69", b'i')
        raw_data = raw_data.replace(b"#6a", b'j')
        raw_data = raw_data.replace(b"#6b", b'k')
        raw_data = raw_data.replace(b"#6c", b'l')
        raw_data = raw_data.replace(b"#6d", b'm')
        raw_data = raw_data.replace(b"#6e", b'n')
        raw_data = raw_data.replace(b"#6f", b'o')
        raw_data = raw_data.replace(b"#70", b'p')
        raw_data = raw_data.replace(b"#71", b'q')
        raw_data = raw_data.replace(b"#72", b'r')
        raw_data = raw_data.replace(b"#73", b's')
        raw_data = raw_data.replace(b"#74", b't')
        raw_data = raw_data.replace(b"#75", b'u')
        raw_data = raw_data.replace(b"#76", b'v')
        raw_data = raw_data.replace(b"#77", b'w')
        raw_data = raw_data.replace(b"#78", b'x')
        raw_data = raw_data.replace(b"#79", b'y')
        raw_data = raw_data.replace(b"#7a", b'z')
        return raw_data
