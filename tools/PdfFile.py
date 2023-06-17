from re import findall


class PdfFile:
    """
    Gets the object structure of a PDF file.
    """
    def __init__(self, raw_file: bytes):
        self.raw_bytes: bytes = raw_file
        self.objects_count: int = 0
        self.object_ids: list = list()
        self.version: str = ""

    def get_structure(self):
        # get version
        version_re = rb"\%PDF-[0-9]\.[0-9]"
        version_result = findall(pattern=version_re, string=self.raw_bytes)
        self.version = version_result[0].decode('utf-8').replace('%PDF-', '')

        # get object count
        object_re = rb"\d{1,9} \d obj"
        object_result = findall(pattern=object_re, string=self.raw_bytes)

        # eliminate duplicate object ids
        self.object_ids = list(set(object_result))
        self.objects_count = len(self.object_ids)
