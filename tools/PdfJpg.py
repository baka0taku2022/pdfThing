from tkinter import *
from io import BytesIO
import PIL.ImageTk
import PIL.Image as Img

class PdfJpg:
    def __init__(self, root: Toplevel, raw_object: bytes):
        self.raw = raw_object
        self.root = root

        # define widgets
        self.top = Toplevel(master=self.root)
        self.img_obj = Img.open(BytesIO(self.raw))
        self.image = PIL.ImageTk.PhotoImage(image=self.img_obj)
        self.img_label = Label(master=self.top, image=self.image)
        self.img_label.image = self.image
        # place widgets
        self.img_label.pack()
