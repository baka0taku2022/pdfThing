from tkinter import Tk, StringVar, Label, Entry, Button, filedialog, SUNKEN, Frame, LEFT, RIGHT
from tools.PdfFile import PdfFile
from tools.ObjectBrowser import ObjectBrowser
from tools.ObjectTree import ObjectTree
from typing import IO

# make root window
program_title = "pdfThing 0.4"
root = Tk()
root.title(program_title)
entry_text = StringVar()


def file_button_handler() -> None:
    """
    Display open file dialog.
    :return: None
    """
    file_name: IO | None = filedialog.askopenfile(title="Open PDF File", parent=root, initialdir="/",
                                                  filetypes=[("PDF File", "*.pdf")])
    # refresh window
    root.update_idletasks()

    #
    if file_name is not None:
        entry_text.set(str(file_name.name))


def ob_button_handler() -> None:
    """
    Open file, read bytes, get PDF structure and enter object browser
    :return: None
    """
    if entry_text.get() is not None:
        try:
            with open(entry_text.get(), "rb") as fh:
                raw_bytes: bytes = fh.read()
                fh.close()
                pdf = PdfFile(raw_file=raw_bytes)
                pdf.get_structure()
                ObjectBrowser(root=root, pdf_obj=pdf, title=program_title)
        except FileNotFoundError:
            pass


def ot_button_handler() -> None:
    try:
        with open(entry_text.get(), "rb") as fh:
            ObjectTree(root=root, file=fh)
    except FileNotFoundError:
        pass


# create widgets
file_label = Label(master=root, text="Path to PDF")
file_entry = Entry(master=root, width=50, textvariable=entry_text, relief=SUNKEN)
file_button = Button(master=root, text="Select File", command=file_button_handler)
button_frame = Frame(master=root)
file_ob = Button(master=button_frame, text="Enter Object Browser", command=ob_button_handler)
file_ot = Button(master=button_frame, text="Enter Object Tree", command=ot_button_handler)

# place widgets
file_label.grid(row=0, column=0, padx=10, pady=10)
file_entry.grid(row=0, column=1, padx=10, pady=10)
file_button.grid(row=0, column=2, padx=10, pady=10)
button_frame.grid(row=1, column=1)
file_ob.pack(side=LEFT)
file_ot.pack(side=RIGHT)
# Start graphics
if __name__ == '__main__':
    root.mainloop()
