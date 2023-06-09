from tkinter import Tk, StringVar, Label, Entry, Button, filedialog, SUNKEN
from tools.PdfFile import PdfFile
from tools.ObjectBrowser import ObjectBrowser
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


def ok_button_handler() -> None:
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


# create widgets
file_label = Label(master=root, text="Path to PDF")
file_entry = Entry(master=root, width=50, textvariable=entry_text, relief=SUNKEN)
file_button = Button(master=root, text="Select File", command=file_button_handler)
file_ok = Button(master=root, text="Enter Object Browser", width=50, command=ok_button_handler)

# place widgets
file_label.grid(row=0, column=0, padx=10, pady=10)
file_entry.grid(row=0, column=1, padx=10, pady=10)
file_button.grid(row=0, column=2, padx=10, pady=10)
file_ok.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

# Start graphics
if __name__ == '__main__':
    root.mainloop()
