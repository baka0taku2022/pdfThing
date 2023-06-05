import binascii
import zlib
import struct


class PdfObject:
    def __init__(self, raw_object: bytes):
        self.raw_object: bytes = raw_object
        self.object_header: bytes = b''
        self.object_type: bytes = b''
        self.object_body: bytes = b''
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

    def parse_object(self):
        self.object_header = self.raw_object[self.raw_object.find(b"<<") + 2: self.raw_object.find(b">>")]
        self.object_body = self.raw_object[self.raw_object.find(b">>") + 2:]

    def parse_header(self):
        # get object type from header
        if self.object_header.replace(b'\r', b' ').replace(b'\n', b' ').find(b'/Type') != -1:
            obj_type: bytes = self.object_header.replace(b'\n', b' ').replace(b'\r', b' ')
            obj_type = obj_type[self.object_header.find(b'/Type') + 7:]
            obj_type = obj_type[:obj_type.find(b' ')]
            self.object_type = obj_type
        else:
            self.object_type = b'N/A'

    def check_filters(self):
        # check for filters
        if self.object_header.find(b'/Filter') != -1:
            self.filter = True

    def flate_decode_action(self):
        self.flate_decode = True
        if self.decoded_stream == b'':
            stream = self.object_body[self.object_body.find(b'stream') + 6:]
            stream = stream[: stream.find(b'endstream')]
            stream = stream.strip(b'\r\n')
        else:
            stream = self.decoded_stream
        try:
            self.decoded_stream: bytes = zlib.decompress(stream)
        except zlib.error:
            pass
        self.object_type: bytes = b'N/A'

    def ascii_hex_decode_action(self):
        self.ascii_hex_decode = True
        if self.decoded_stream == b'':
            stream = self.object_body[self.object_body.find(b'stream') + 6:]
            stream = stream[: stream.find(b'endstream')]
            stream = stream.strip(b'\r\n')
        else:
            stream = self.decoded_stream
        self.decoded_stream = binascii.unhexlify(stream.replace(b'>', b'').replace(b' ', b''))

    def ascii_85_decode_action(self):
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

    def run_length_decode_action(self):
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

    def lzw_decode_action(self):
        self.lzw_decode = True

    def jbig2_decode_action(self):
        self.jbig2_decode = True

    def ccitt_fax_decode_action(self):
        self.ccitt_fax_decode = True