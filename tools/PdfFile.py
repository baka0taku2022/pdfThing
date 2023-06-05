import re




class PdfFile(object):
    def __init__(self, raw_file: bytes):
        self.raw_bytes = raw_file
        self.objects_count: int = 0
        self.object_ids: list = list()
        self.version: str = ""
        self.objects_dict: dict = dict()
        self.obfuscated: bool = False

    def get_structure(self):
        # get version
        version_re = b"\%PDF-[0-9]\.[0-9]"
        version_result = re.findall(pattern=version_re, string=self.raw_bytes)
        self.version = version_result[0].decode('utf-8').replace('%PDF-', '')

        # get object count
        object_re = b"\d{1,4} \d obj"
        object_result = re.findall(pattern=object_re, string=self.raw_bytes)
        self.object_ids = list(set(object_result))
        self.objects_count = len(self.object_ids)

        # get all objects
        for obj_id in self.object_ids:
            intro_size = len(obj_id)
            obj_start = self.raw_bytes.find(obj_id)
            obj = self.raw_bytes[obj_start + intro_size:]
            obj = obj[:obj.find(b"endobj")]
            self.objects_dict[obj_id] = obj

    def is_obfuscated(self):
        regex = b"#[a-fA-F0-9][a-fA-F0-9]"
        chars = re.findall(regex, self.raw_bytes)
        if len(chars) > 0:
            self.obfuscated = True

    def deobfuscate(self):
        raw_data = self.raw_bytes
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
        self.raw_bytes = raw_data
