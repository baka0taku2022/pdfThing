from tkinter import filedialog
from tkinter import *
from tools import PdfFile, ObjectBrowser

# make root window
program_title = "pdfThing 0.3"
root = Tk()
root.title(program_title)


def file_button_handler():
    file_name = filedialog.askopenfile(title="Open PDF File", parent=root, initialdir="/",
                                       filetypes=[("PDF File", "*.pdf")])
    root.update_idletasks()
    if file_name is not None:
        entry_text.set(str(file_name.name))


def ok_button_handler():
    if entry_text.get() is not None:
        try:
            with open(entry_text.get(), "rb") as fh:
                raw_bytes = fh.read()
                fh.close()
                pdf = PdfFile.PdfFile(raw_file=raw_bytes)
                pdf.get_structure()
                ObjectBrowser.ObjectBrowser(root=root, pdf_obj=pdf, title=program_title)
        except FileNotFoundError:
            pass


# vars
entry_text = StringVar()
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

if __name__ == '__main__':
    root.mainloop()
