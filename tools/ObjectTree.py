from re import findall, compile
from base64 import a85decode
from binascii import unhexlify
from tkinter import Tk, Toplevel, Frame, VERTICAL, Scrollbar, Button, LEFT, BOTH, RIGHT, END, Label, SUNKEN, Text, \
    DISABLED, NORMAL
from tkinter.ttk import Treeview
from tkinter.messagebox import showerror, showinfo
from typing import BinaryIO
from zlib import decompress

from tools.lzw import lzwdecode


class ObjectTree:
    def __init__(self, root: Tk, file: BinaryIO):
        self.raw: BinaryIO = file
        self.root: Tk = root
        self.pdf_version: bytes = b''
        self.pdf_objects: list[PdfObject] = list()
        self.object_ids: list[bytes] = list()
        self.has_duplicates: bool = False
        self.in_object: bool = False
        self.current_object: PdfObject

        # common regex
        self.pdf_start = compile(rb'PDF-\d\.\d')
        self.obj_start = compile(rb'\d{1,9} \d obj')
        self.obj_end = compile(rb'endobj')

        # read file by line
        for line in self.raw:
            if len(findall(self.pdf_start, line)) > 0:
                self.pdf_version = self.pdf_version + line.strip(rb'%').rstrip()
            elif len(findall(self.obj_start, line)) > 0:
                # check for improper endobj and append current object if still in object
                if self.in_object:
                    self.pdf_objects.append(self.current_object)
                self.in_object = True
                self.current_object = PdfObject()
                matches = findall(self.obj_start, line)
                if len(matches) >= 1:
                    self.current_object.object_id = matches[0]
                    self.object_ids.append(matches[0])
                    self.current_object.object = self.current_object.object + line
                else:
                    pass
            elif len(findall(self.obj_end, line)) > 0:
                self.in_object = False
                self.current_object.object = self.current_object.object + line.replace(b'endobj', b'')
                self.current_object.is_obfuscated()
                if self.current_object.obfuscated:
                    self.current_object.deobfuscate()
                self.current_object.parse_object()
                self.current_object.parse_header()
                self.pdf_objects.append(self.current_object)
            elif self.in_object:
                self.current_object.object = self.current_object.object + line

        # find duplicates as sanity check otherwise pdf is malformed
        id_count = len(self.object_ids)
        check_count = len(set(self.object_ids))
        if check_count < id_count:
            self.has_duplicates = True
            showerror(title='Error', message="PDF has duplicate objects.\nSome objects unavailable.")

        # create widgets
        self.top = Toplevel(master=self.root)
        self.tree_frame = Frame(master=self.top)
        self.tv = Treeview(master=self.tree_frame, height=25)
        self.tree_scroll = Scrollbar(self.tree_frame, orient=VERTICAL, command=self.tv.yview)
        self.tv.config(yscrollcommand=self.tree_scroll.set)
        self.button_frame = Frame(master=self.top)
        self.view_raw_header = Button(master=self.button_frame, text="View Raw Header", command=self.raw_header_handler)
        self.view_decoded_stream = Button(master=self.button_frame, text="View Decoded Stream",
                                          command=self.decoded_stream_handler)

        # place widgets
        self.tree_frame.grid(column=0, row=0)
        self.tv.pack(side=LEFT, fill=BOTH)
        self.tree_scroll.pack(side=RIGHT, fill=BOTH)
        self.button_frame.grid(column=1, row=0)
        self.view_raw_header.pack()
        self.view_decoded_stream.pack()

        # root of tree is file path
        self.tv.insert(parent='', index=0, iid='item0', text=self.raw.name[self.raw.name.rfind(r'/') + 1:])
        # Add object list
        x = 1

        for obj in sorted(list(self.pdf_objects), key=lambda pdf_object: pdf_object.object_id):
            self.tv.insert(parent='item0', index=END, iid='item' + str(x), text=obj.object_id)
            if len(obj.ref_obj) > 0:
                for ref in obj.ref_obj:
                    self.tv.insert(parent='item' + str(x), index=2, text=ref)
            x += 1

    def raw_header_handler(self):
        current_item = self.tv.focus()
        obj_id = self.tv.item(current_item, 'text')
        if obj_id.find(b'R') != -1:
            obj_id = obj_id.replace(b'R', b'obj')
        for obj in self.pdf_objects:
            if obj.object_id == obj_id:
                if obj.has_js:
                    showinfo(title="Info", message="Object contains or references JS.")
                win: Toplevel = Toplevel(master=self.top)
                if obj.header != b'':
                    raw_header: Label = Label(master=win, text=obj.header)
                    raw_header.pack()

    def decoded_stream_handler(self):
        current_item = self.tv.focus()
        obj_id = self.tv.item(current_item, 'text')
        if obj_id.find(b'R') != -1:
            obj_id = obj_id.replace(b'R', b'obj')
        for obj in self.pdf_objects:
            if obj.object_id == obj_id:
                if obj.has_filters:
                    for fltr in obj.filters:
                        if len(findall(rb'FlateDecode', fltr)) > 0:
                            obj.flate_decode_action()
                        elif len(findall(rb'ASCIIHexDecode', fltr)) > 0:
                            obj.ascii_hex_decode_action()
                        elif len(findall(rb'ASCII85Decode', fltr)) > 0:
                            obj.ascii_85_decode_action()
                        elif len(findall(rb'RunLengthDecode', fltr)) > 0:
                            obj.run_length_decode_action()
                        elif len(findall(rb'LZWDecode', fltr)) > 0:
                            obj.lzw_decode_action()
                        elif len(findall(rb'JBIG2Decode', fltr)) > 0:
                            obj.jbig2_decode_action()
                        elif len(findall(rb'CCITTFaxDecode', fltr)) > 0:
                            obj.ccitt_fax_decode_action()
                        elif len(findall(rb'DCTDecode', fltr)) > 0:
                            obj.dct_decode_action()
                win = Toplevel(master=self.top)
                stream_frame = Frame(master=win)
                stream = Text(master=stream_frame, width=50, height=50, relief=SUNKEN, wrap="word", state=DISABLED)
                if obj.decoded_stream == b'':
                    stream.configure(state=NORMAL)
                    stream.insert(END, obj.stream)
                    stream.configure(state=DISABLED)
                else:
                    stream.configure(state=NORMAL)
                    stream.insert(END, obj.decoded_stream)
                    stream.configure(state=DISABLED)
                stream.pack()
                stream_frame.grid(column=0, row=0)


class PdfObject:
    def __init__(self):
        self.header: bytes = b''
        self.object: bytes = b''
        self.stream: bytes = b''
        self.decoded_stream: bytes = b''
        self.object_id: bytes = b''
        self.ref_obj: list[bytes] = list()
        self.filters: list[bytes] = list()
        self.obj_type: bytes = b''
        self.has_js: bool = False
        self.obfuscated: bool = False
        self.has_filters: bool = False

    def parse_object(self):
        self.header = self.object[self.object.find(b"<<") + 2: self.object.find(b">>")]
        self.stream = self.object[self.object.find(b">>") + 2:]
        self.stream = self.stream[self.stream.find(b'stream') + 6: self.stream.rfind(b'endstream')]

    def is_obfuscated(self) -> None:
        regex = b"#[a-fA-F0-9][a-fA-F0-9]"
        chars = findall(regex, self.object)
        if len(chars) > 0:
            self.obfuscated = True

    def deobfuscate(self) -> None:
        raw_data = self.object
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
        self.object = raw_data

    def parse_header(self):
        # look for referenced objects
        self.ref_obj = findall(br"\d{1,9} \d R", self.header)
        # look for javascript marker
        if len(findall(br"JavaScript", self.header)) > 0 or len(findall(rb'JS', self.header)) > 0:
            self.has_js = True
        if len(findall(br"Filter", self.header)) > 0:
            self.has_filters = True
        if self.has_filters:
            filters: bytes | list[bytes] = self.header[self.header.find(b'Filter') + 6:]
            filters = filters.replace(b'\r', b'').replace(b'\n', b' ')
            filters = filters.split(b' ')
            self.filters = filters

    def flate_decode_action(self):
        if self.decoded_stream == b'':
            self.decoded_stream = decompress(self.stream.strip())
        else:
            self.decoded_stream = decompress(self.decoded_stream)

    def ascii_hex_decode_action(self):
        if self.decoded_stream == b'':
            self.decoded_stream = unhexlify(self.stream.strip())
        else:
            self.decoded_stream = unhexlify(self.decoded_stream.replace(b'>', b'').replace(b' ', b''))

    def ascii_85_decode_action(self):
        if self.decoded_stream == b'':
            self.decoded_stream = a85decode(b=self.stream.strip(), adobe=True)
        else:
            self.decoded_stream = a85decode(b=self.decoded_stream, adobe=True)

    def run_length_decode_action(self):
        # see LICENSE pdfminer.six this is his code
        # https://github.com/euske/pdfminer/blob/master/pdfminer/runlength.py
        if self.decoded_stream == b'':
            stream = self.stream.strip()
        else:
            stream = self.decoded_stream
        decoded = b''
        i = 0
        while i < len(stream):
            # print('data[%d]=:%d:' % (i,ord(data[i])))
            length = stream[i]
            if length == 128:
                break
            if 0 <= length < 128:
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
        if self.decoded_stream == b'':
            self.decoded_stream = lzwdecode(data=self.stream.strip())
        else:
            self.decoded_stream = lzwdecode(data=self.decoded_stream)

    def jbig2_decode_action(self):
        if self.decoded_stream == b'':
            self.decoded_stream = self.stream.strip()
        else:
            self.decoded_stream = self.decoded_stream

    def ccitt_fax_decode_action(self):
        if self.decoded_stream == b'':
            self.decoded_stream = self.stream.strip()
        else:
            self.decoded_stream = self.decoded_stream

    def dct_decode_action(self):
        if self.decoded_stream == b'':
            self.decoded_stream = self.stream.strip()
        else:
            self.decoded_stream = self.decoded_stream
