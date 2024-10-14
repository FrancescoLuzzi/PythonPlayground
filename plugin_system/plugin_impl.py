from tkinter import messagebox


def after_login(name: str, id: int) -> int:
    return len(messagebox.showinfo(name, str(id)))
