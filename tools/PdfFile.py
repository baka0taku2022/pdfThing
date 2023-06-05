import re


class PdfFile(object):
    def __init__(self, raw_file: bytes):
        self.raw_bytes = raw_file
        self.objects_count: int = 0
        self.object_ids: list = list()
        self.version: str = ""
        self.objects_dict: dict = dict()

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
