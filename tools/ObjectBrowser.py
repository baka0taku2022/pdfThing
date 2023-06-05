from tkinter import *
from tkinter.filedialog import asksaveasfile
from tkinter.messagebox import showinfo
from tools.PdfFile import PdfFile
from tools.PdfObject import PdfObject


class ObjectBrowser:
    def __init__(self, root: Tk, pdf_obj: PdfFile, title: str):
        self.top = Toplevel(master=root)
        self.top.title(title + " - Object Browser")
        self.pdf = pdf_obj
        self.object_type_var = StringVar()
        self.filter_var = StringVar()
        self.flate_var = StringVar()
        self.ascii_hex_var = StringVar()
        self.ascii85_var = StringVar()
        self.run_length_var = StringVar()
        self.lzw_var = StringVar()
        self.jbig2_var = StringVar()
        self.current_header: bytes = b''
        self.current_object: bytes = b''

        # define widgets
        self.pdf_version_label = Label(master=self.top, text="PDF Version")
        self.pdf_version = Label(master=self.top, text=self.pdf.version, relief=SUNKEN, width=20)
        self.obj_frame = Frame(master=self.top)
        self.obj_list_label = Label(master=self.top, text="Object ID")
        self.obj_list = Listbox(master=self.obj_frame, height=30)
        self.obj_list.bind(sequence='<<ListboxSelect>>', func=self.list_handle)
        self.obj_list_scroll = Scrollbar(master=self.obj_frame, orient=VERTICAL)
        self.obj_list.config(yscrollcommand=self.obj_list_scroll.set)
        self.obj_list_scroll.config(command=self.obj_list.yview)
        self.object_contents_label = Label(master=self.top, text="Object Contents")
        self.content_frame = Frame(master=self.top)
        self.object_contents = Text(master=self.content_frame, width=50, height=30, wrap='word',
                                    state=DISABLED)
        self.object_contents_scroll = Scrollbar(master=self.content_frame, orient=VERTICAL)
        self.object_contents.config(yscrollcommand=self.object_contents_scroll.set)
        self.object_contents_scroll.config(command=self.object_contents.yview)
        self.object_type_label = Label(master=self.top, text='Object Type')
        self.object_type = Label(master=self.top, textvariable=self.object_type_var, width=20,
                                 relief=SUNKEN)
        self.filter_label = Label(master=self.top, text="Filters?")
        self.filter = Label(master=self.top, textvariable=self.filter_var, relief=SUNKEN, width=20)
        self.flate_label = Label(master=self.top, text="FlateDecode?")
        self.flate = Label(master=self.top, textvariable=self.flate_var, relief=SUNKEN, width=20)
        self.ascii_hex_label = Label(master=self.top, text="AsciiHexDecode?")
        self.ascii_hex = Label(master=self.top, textvariable=self.ascii_hex_var, relief=SUNKEN,
                               width=20)
        self.ascii_85_label = Label(master=self.top, text="Ascii85Decode?")
        self.ascii_85 = Label(master=self.top, textvariable=self.ascii85_var, relief=SUNKEN, width=20)
        self.run_length_label = Label(master=self.top, text="RunLengthDecode?")
        self.run_length = Label(master=self.top, textvariable=self.run_length_var, relief=SUNKEN,
                                width=20)
        self.lzw_label = Label(master=self.top, text="LZWDecode?")
        self.lzw = Label(master=self.top, textvariable=self.lzw_var, relief=SUNKEN, width=20)
        self.jbig2_label = Label(master=self.top, text="JBig2Decode?")
        self.jbig2 = Label(master=self.top, textvariable=self.jbig2_var, relief=SUNKEN, width=20)
        self.raw_header_button = Button(master=self.top, text="Raw Object Header",
                                        command=self.raw_header_button_handler)
        self.save_body_button = Button(master=self.top, text="Save Object Body",
                                       command=self.save_object_body_button_handler)

        # add objects to list
        self.obj_list.insert(END, *sorted(list(self.pdf.objects_dict.keys())))

        # place widgets
        self.pdf_version_label.grid(column=0, row=0, padx=5, pady=5)
        self.pdf_version.grid(column=1, row=0, padx=5, pady=5)
        self.obj_list.pack(side=LEFT)
        self.obj_list_scroll.pack(side=RIGHT, fill=BOTH)
        self.obj_list_label.grid(column=0, row=1, padx=5, pady=5)
        self.obj_frame.grid(column=0, row=2, rowspan=5, padx=5, pady=5)
        self.object_contents_label.grid(column=1, row=1, padx=5, pady=5)
        self.content_frame.grid(column=1, row=2, rowspan=5, padx=5, pady=5)
        self.object_contents.pack(side=LEFT)
        self.object_contents_scroll.pack(side=RIGHT, fill=BOTH)
        self.object_type_label.grid(column=2, row=1, padx=5, pady=5)
        self.object_type.grid(column=3, row=1, padx=5, pady=5)
        self.filter_label.grid(column=2, row=2, padx=5, pady=5)
        self.filter.grid(column=3, row=2, padx=5, pady=5)
        self.flate_label.grid(column=2, row=3, padx=5, pady=5)
        self.flate.grid(column=3, row=3, padx=5, pady=5)
        self.ascii_hex_label.grid(column=2, row=4, padx=5, pady=5)
        self.ascii_hex.grid(column=3, row=4, padx=5, pady=5)
        self.ascii_85_label.grid(column=2, row=5, padx=5, pady=5)
        self.ascii_85.grid(column=3, row=5, padx=5, pady=5)
        self.run_length_label.grid(column=2, row=6, padx=5, pady=5)
        self.run_length.grid(column=3, row=6, padx=5, pady=5)
        self.lzw_label.grid(column=2, row=7, padx=5, pady=5)
        self.lzw.grid(column=3, row=7, padx=5, pady=5)
        self.jbig2_label.grid(column=2, row=8, padx=5, pady=5)
        self.jbig2.grid(column=3, row=8, padx=5, pady=5)
        self.raw_header_button.grid(column=3, row=9, padx=5, pady=5)
        self.save_body_button.grid(column=2, row=9, padx=5, pady=5)

    def list_handle(self, event):
        try:
            self.object_contents.configure(state=NORMAL)
            self.object_contents.get(1.0, END)
            self.object_contents.delete(1.0, END)
            self.object_contents.configure(state=DISABLED)
        except TclError:
            pass
        selected_index: tuple = self.obj_list.curselection()

        if selected_index != ():
            selected_text: str = self.obj_list.get(selected_index[0])
            contents = self.pdf.objects_dict.get(selected_text)
            pdf_object: PdfObject = PdfObject(raw_object=contents)
            pdf_object.parse_object()
            pdf_object.parse_header()
            pdf_object.check_filters()
            if pdf_object.filter:
                # extract filter section
                raw_filters = pdf_object.object_header[pdf_object.object_header.find(b'/Filter') + 7:]
                filters = raw_filters.split(b' ')
                # decode filters
                for filter_text in filters:
                    if filter_text.find(b'/FlateDecode') != -1:
                        pdf_object.flate_decode_action()
                    elif filter_text.find(b'/ASCIIHexDecode') != -1:
                        pdf_object.ascii_hex_decode_action()
                    elif filter_text.find(b'/ASCII85Decode') != -1:
                        pdf_object.ascii_85_decode_action()
                    elif filter_text.find(b'/RunLengthDecode') != -1:
                        pdf_object.run_length_decode_action()
                    elif filter_text.find(b'/LZWDecode') != -1:
                        pdf_object.lzw_decode_action()
                    elif filter_text.find(b'/JBIG2Decode') != -1:
                        pdf_object.jbig2_decode_action()
        try:
            # set stringvars
            self.object_type_var.set(pdf_object.object_type)
            self.filter_var.set(str(pdf_object.filter))
            self.flate_var.set(str(pdf_object.flate_decode))
            self.ascii_hex_var.set(str(pdf_object.ascii_hex_decode))
            self.ascii85_var.set(str(pdf_object.ascii_85_decode))
            self.run_length_var.set(str(pdf_object.run_length_decode))
            self.lzw_var.set(str(pdf_object.lzw_decode))
            self.jbig2_var.set(str(pdf_object.jbig2_decode))

            if pdf_object.decoded_stream != b'':
                self.object_contents.configure(state=NORMAL)
                self.object_contents.insert(END, pdf_object.decoded_stream)
                self.object_contents.configure(state=DISABLED)
                self.current_object = pdf_object.decoded_stream
            else:
                self.object_contents.configure(state=NORMAL)
                self.object_contents.insert(END, pdf_object.object_body)
                self.object_contents.configure(state=DISABLED)
                self.current_object = pdf_object.object_body
            self.current_header = pdf_object.object_header

        except UnboundLocalError:
            pass

    def raw_header_button_handler(self):
        showinfo(title="Raw Header", message=self.current_header.decode(encoding="utf-8"))

    def save_object_body_button_handler(self):
        file = asksaveasfile(mode="wb")
        if file is not None:
            file.write(self.current_object)
            file.close()
