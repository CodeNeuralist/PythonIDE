from tkinter import *
from tkinter import filedialog, ttk
import os
import subprocess
import re

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip = Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = Label(self.tooltip, text=self.text, background="lightyellow", relief="solid", borderwidth=1)
        label.pack()

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()

def execute():
    current_tab = notebook.index(notebook.select())
    current_text = text_areas[current_tab].get('1.0', END)
    with open(f'run_{current_tab}.py', 'w', encoding='utf-8') as f:
        f.write(current_text)

    terminal.delete('1.0', END)
    terminal.insert(END, f">> python run_{current_tab}.py\n")
    process = subprocess.Popen(['python', f'run_{current_tab}.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    terminal.insert(END, output.decode("utf-8"))
    terminal.insert(END, error.decode("utf-8"))

def open_file():
    filename = filedialog.askopenfilename()
    if filename:
        with open(filename, 'r') as f:
            content = f.read()
            add_tab(content, filename)
            changes()

def create_file():
    filename = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py"), ("All Files", "*.*")])
    if filename:
        add_tab(filename=filename)

def add_tab(content="", filename=""):
    new_tab = ttk.Frame(notebook)
    notebook.add(new_tab, text=os.path.basename(filename) if filename else "Untitled")
    text_area = Text(new_tab, background=background, foreground=normal, insertbackground=normal, relief=FLAT, borderwidth=0, font=font)
    text_area.pack(side=LEFT, fill=BOTH, expand=1)
    text_area.insert(END, content)
    scroll = Scrollbar(new_tab, command=text_area.yview)
    scroll.pack(side=RIGHT, fill=Y)
    text_area.config(yscrollcommand=scroll.set)
    text_areas.append(text_area)
    text_area.bind('<KeyRelease>', lambda event: changes())
    text_area.bind('<FocusIn>', lambda event: changes())

def open_folder():
    foldername = filedialog.askdirectory()
    if foldername:
        tree.delete(*tree.get_children())
        populate_tree(tree, foldername)

def save_file():
    current_tab = notebook.index(notebook.select())
    current_text = text_areas[current_tab].get('1.0', END)
    with open(f'run_{current_tab}.py', 'w', encoding='utf-8') as f:
        f.write(current_text)

def changes(event=None):
    current_tab = notebook.index(notebook.select())
    global previousText
    if text_areas[current_tab].get('1.0', END) == previousText.get(current_tab, ''):
        return

    for tag in text_areas[current_tab].tag_names():
        text_areas[current_tab].tag_remove(tag, "1.0", "end")

    i = 0
    for pattern, color in repl:
        for start, end in search_re(pattern, text_areas[current_tab].get('1.0', END)):
            text_areas[current_tab].tag_add(f'{i}', start, end)
            text_areas[current_tab].tag_config(f'{i}', foreground=color)
            i += 1

    previousText[current_tab] = text_areas[current_tab].get('1.0', END)
    update_line_numbers()


def search_re(pattern, text):
    matches = []
    text = text.splitlines()
    for i, line in enumerate(text):
        for match in re.finditer(pattern, line):
            matches.append(
                (f"{i + 1}.{match.start()}", f"{i + 1}.{match.end()}")
            )
    return matches

def rgb(rgb):
    return "#%02x%02x%02x" % rgb

def update_line_numbers():
    current_tab = notebook.index(notebook.select())
    line_numbers.config(state=NORMAL)
    line_numbers.delete('1.0', END)
    text = text_areas[current_tab].get('1.0', 'end-1c')
    lines = text.split('\n')
    for i, line in enumerate(lines, start=1):
        line_numbers.insert(END, f'{i}\n')
    line_numbers.config(state=DISABLED)

def populate_tree(tree, folder):
    if os.path.isdir(folder):
        tree.heading('#0', text=folder, anchor='w')
        root_dir = tree.insert('', 'end', text=folder, open=True)
        for item in os.listdir(folder):
            path = os.path.join(folder, item)
            if os.path.isdir(path):
                populate_tree(tree, path)
            else:
                tree.insert(root_dir, 'end', text=item)

root = Tk()
root.geometry('950x500')
root.title('Редактор кода')
previousText = {}
text_areas = []

normal = rgb((234, 234, 234))
keywords = rgb((234, 95, 95))
comments = rgb((95, 234, 165))
string = rgb((234, 162, 95))
function = rgb((95, 211, 234))
background = rgb((42, 42, 42))
font = 'Consolas 15'

repl = [
    ['(^| )(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)($| )', keywords],
    ['".*?"', string],
    ['\'.*?\'', string],
    ['#.*?$', comments],
]

menubar = Menu(root)

file_menu = Menu(menubar, tearoff=0)
file_menu.add_command(label="Открыть", command=open_file)
file_menu.add_command(label="Создать", command=create_file)
file_menu.add_command(label="Сохранить", command=save_file)
file_menu.add_command(label="Выход", command=root.quit)
menubar.add_cascade(label="Файл", menu=file_menu)

run_menu = Menu(menubar, tearoff=0)
run_menu.add_command(label="Запустить", command=execute)
menubar.add_cascade(label="Выполнить", menu=run_menu)

root.config(menu=menubar)

editor_frame = Frame(root)
editor_frame.pack(side=TOP, fill=BOTH, expand=1)

terminal_frame = PanedWindow(root, orient=VERTICAL, sashrelief=RAISED, sashwidth=4, sashpad=4, handlepad=4)
terminal_frame.pack(side=BOTTOM, fill=BOTH, expand=1)
terminal_frame.pack_propagate(False)

terminal = Text(terminal_frame, background=background, foreground=normal, insertbackground=normal, relief=FLAT, borderwidth=10, font=font)
terminal_frame.add(terminal)

line_number_frame = Text(editor_frame, width=4, padx=4, takefocus=0, border=0, background=background, foreground=normal, font=font)
line_number_frame.pack(side=LEFT, fill=Y)

notebook = ttk.Notebook(editor_frame)
notebook.pack(side=LEFT, fill=BOTH, expand=1)

scroll = Scrollbar(editor_frame, command=line_number_frame.yview)
scroll.pack(side=RIGHT, fill=Y)
line_number_frame.config(yscrollcommand=scroll.set)

Tooltip(file_menu, "Открыть файл")
Tooltip(file_menu, "Создать файл")
Tooltip(file_menu, "Сохранить файл")
Tooltip(file_menu, "Выход")
Tooltip(run_menu, "Запустить программу")

line_numbers = Text(line_number_frame, width=4, padx=4, takefocus=0, border=0, background=background, foreground=normal, font=font)
line_numbers.pack(side=LEFT, fill=Y)
line_numbers.insert(END, '1\n')
line_numbers.config(state=DISABLED)

tree_frame = Frame(root)
tree_frame.pack(side=LEFT, fill=Y)

tree_scroll = Scrollbar(tree_frame)
tree_scroll.pack(side=RIGHT, fill=Y)

tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set)
tree.pack(side=LEFT, fill=BOTH, expand=1)

tree_scroll.config(command=tree.yview)

root.mainloop()
