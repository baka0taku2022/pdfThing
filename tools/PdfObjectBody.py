from tkinter import *


class PdfObjectBody:
    def __init__(self, object_body: bytes, parent: Toplevel):
        self.obj_body = object_body
        self.root = parent

        # define widgets
        self.top = Toplevel(master=self.root)
        self.top.title(string="PDF Raw Object Body Viewer")
        self.obj_frame = Frame(master=self.top)
        self.body = Text(master=self.obj_frame, width=50, height=50, relief=SUNKEN, wrap="word", state=DISABLED)
        self.body_scroll = Scrollbar(master=self.obj_frame, orient=VERTICAL)
        self.body.config(yscrollcommand=self.body_scroll.set)
        self.body_scroll.config(command=self.body.yview)

        # write data to Text box and disable
        self.body.configure(state=NORMAL)
        self.body.insert(END, self.obj_body)
        self.body.configure(state=DISABLED)

        # place widgets
        self.obj_frame.pack()
        self.body.pack(side=LEFT)
        self.body_scroll.pack(side=RIGHT, fill=BOTH)
