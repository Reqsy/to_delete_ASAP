import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import fitz
from unipdfconv import Unipdfconv
from PIL import Image, ImageTk
import shutil
from watcher import DirectoryWatcher

converter = Unipdfconv()
images = []
raw_images = []
selected_file = None  # Переменная для хранения пути к выбранному файлу
if not os.path.exists("Документы"):
    os.makedirs("Документы")
os.chdir("Документы")
current_directory = os.getcwd()  # Переменная для хранения текущей директории
working_file_path = ""
In_work = False


def scan_directory(directory=None, element_id=None):
    contents = os.listdir(directory)
    contents.sort(key=lambda x: (os.path.isdir(os.path.join(current_directory, x)), x))

    # Сортируем содержимое: сначала директории, потом файлы
    contents.sort(key=lambda x: (os.path.isdir(os.path.join(current_directory, x)), x))

    for item in contents:
        item_path = os.path.join(current_directory, item)
        if os.path.isdir(item_path):
            # Если элемент является директорией, добавляем метку и рекурсивно отображаем ее содержимое
            content_listbox.insert(element_id + 1, f"         📁 {item}")
        elif item.endswith((".pdf", ".odt", ".rtf", ".docx", ".doc")):
            # Если элемент является файлом, добавляем метку с его именем
            content_listbox.insert(element_id + 1, f"         📄 {item}")


def show_directory_contents(directory=None):
    global current_directory

    if directory is not None:
        current_directory = directory

    # Очищаем содержимое списка файлов
    content_listbox.delete(0, tk.END)

    # Выводим текущую директорию
    # content_listbox.insert(tk.END, f"Текущая директория: {current_directory}")

    # Получаем содержимое текущей директории
    contents = os.listdir(current_directory)

    # Сортируем содержимое: сначала директории, потом файлы
    contents.sort(key=lambda x: (os.path.isdir(os.path.join(current_directory, x)), x))

    for item in contents:
        item_path = os.path.join(current_directory, item)
        if os.path.isdir(item_path):
            # Если элемент является директорией, добавляем метку и рекурсивно отображаем ее содержимое
            content_listbox.insert(tk.END, f"📁 {item}")
        elif item.endswith((".pdf", ".odt", ".rtf", ".docx", ".doc")):
            # Если элемент является файлом, добавляем метку с его именем
            content_listbox.insert(tk.END, f"📄 {item}")


def close_folder(el_id):
    while content_listbox.get(el_id + 1).startswith(f"         "):
        content_listbox.delete(el_id + 1)


def user_add_file():
    file_path = filedialog.askopenfilename()
    path = os.getcwd()
    shutil.copy(file_path, os.path.join(path, os.path.basename(file_path)))
    # messagebox.showinfo("Добавление файла", "Файл успешно добавлен")


def select_file(event):
    global selected_file
    element_id = content_listbox.curselection()[0]
    selected_file = content_listbox.get(element_id)
    if selected_file.startswith("▼"):
        name = content_listbox.get(element_id)
        close_folder(element_id)
        content_listbox.delete(element_id)  # Удаляем выбранный элемент
        content_listbox.insert(element_id, name[1:])
    elif selected_file.startswith("📁"):
        directory = selected_file.split(maxsplit=1)[1]
        name = content_listbox.get(element_id)
        content_listbox.delete(element_id)  # Удаляем выбранный элемент
        content_listbox.insert(element_id, "▼" + name)
        scan_directory(directory, element_id)

    else:
        file_path = get_file_path_from_listbox(element_id)
        preview_file(file_path)


def preview_file(file_path):
    global images, raw_images, converter  # Объявляем глобальные изображения

    if not file_path.endswith(".pdf"):
        file_path = converter.convert_to_pdf(file_path)
        watcher.add_file_to_info(file_path)

    if os.path.isfile(file_path) and (file_path.endswith(".pdf") or file_path.endswith(".PDF")):
        # Открываем PDF файл
        doc = fitz.open(file_path)
        canvas.delete("all")
        # Очищаем список изображений
        images.clear()
        raw_images.clear()
        # Отображаем все страницы PDF файла
        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            pix = page.get_pixmap()
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            raw_images.append(image)
            photo = ImageTk.PhotoImage(image)
            images.append(photo)  # Добавляем фото в список

        doc.close()

        # Устанавливаем размер холста в соответствии с размерами первой страницы

        # Отображаем все страницы на холсте
        y_offset = 0
        for photo in images:
            canvas.create_image(0, y_offset, anchor=tk.NW, image=photo)
            y_offset += photo.height()
        canvas.config(scrollregion=canvas.bbox("all"))
        # Перемещаем прокрутку в начало
        canvas.yview_moveto(0.0)

    else:
        print("Указанный файл не является PDF файлом или не существует.")


def search_files(event=None):
    search_term = search_entry.get().lower()
    if search_term:
        matches = []
        for parent, dirs, files in os.walk(current_directory):
            for file in files:
                if search_term.lower() in file.lower():
                    if parent not in matches:
                        matches.append(parent)
                    matches.append(file)
        show_search_results(matches)
    else:
        show_directory_contents()


def show_search_results(matches):
    content_listbox.delete(0, tk.END)
    for item in matches:
        item_path = os.path.join(current_directory, item)
        if os.path.isdir(item_path):
            content_listbox.insert(tk.END, f"▼📁 {os.path.split(item)[1]}")
        else:
            content_listbox.insert(tk.END, f"         📄 {item}")


def on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


def show_context_menu(event):
    element_id = content_listbox.curselection()[0]
    selected_file = content_listbox.get(element_id)
    if selected_file.startswith(("📄", "         📄")):
        context_menu.post(event.x_root, event.y_root)

    # Получаем индекс выбранного элемента


def on_new_file(file_path):
    global working_file_path

    def _reject():
        global In_work
        newfile_win.destroy()
        In_work = False

    def _add():
        global In_work, helper_window, working_file_path
        newfile_win.destroy()
        rename(file_path)
        root.wait_window(helper_window)
        dir_path = os.path.abspath(filedialog.askdirectory(initialdir=os.getcwd()))
        shutil.move(working_file_path, os.path.join(dir_path, os.path.basename(working_file_path)))
        watcher.add_file_to_info(os.path.join(dir_path, os.path.basename(working_file_path)))
        messagebox.showinfo("Добавление файла", "Файл успешно добавлен")
        In_work = False
        show_directory_contents()

    newfile_win = tk.Toplevel(root)
    newfile_win.title("Переименование файла")
    name_label = tk.Label(newfile_win, text=f'Найден новый файл {os.path.basename(file_path)}')
    name_label.pack(pady=5, padx=10, side=tk.TOP, fill=tk.X)
    name_label = tk.Label(newfile_win, text=f'Добавить файл?')
    name_label.pack(pady=5, padx=10, side=tk.TOP, fill=tk.X)
    btn1 = tk.Button(newfile_win, text="Да", command=_add)
    btn1.pack(pady=5, padx=10, side=tk.LEFT, fill=tk.X, expand=True)
    btn2 = tk.Button(newfile_win, text="Нет", command=_reject)
    btn2.pack(pady=5, padx=10, side=tk.RIGHT, fill=tk.X, expand=True)


def get_file_path_from_listbox(element_id):
    name = content_listbox.get(element_id)
    if name.startswith("📄"):
        path = os.path.join(os.getcwd(), name.split("📄")[1][1:])
    else:
        while not content_listbox.get(element_id).startswith("▼"):
            element_id += -1

        path = os.path.join(os.getcwd(), content_listbox.get(element_id)[2:][1:], name.split("📄")[1][1:])

    return path


def rename_file_from_contex():
    element_id = content_listbox.curselection()[0]
    path = get_file_path_from_listbox(element_id)

    rename(path)


def rename(path_to_file):
    def _on_date_entry_change(event):
        entry_text = user_input1.get()
        if len(entry_text) == 2 or len(entry_text) == 5:
            user_input1.insert(tk.END, '.')

    def _write_to_file(name):
        global working_file_path, helper_window
        new_path_to_file = os.path.join(os.path.dirname(path_to_file), name)

        os.rename(path_to_file, new_path_to_file)
        watcher.add_file_to_info(new_path_to_file)
        working_file_path = new_path_to_file
        win.destroy()
        show_directory_contents()
        helper_window.destroy()
        messagebox.showinfo("Переименование", f'Файл переименован в {name}')

    pack_name = lambda: f'{combobox.get()} от {user_input1.get()} №{user_input2.get()} \'\'{user_input3.get()}\'\'{os.path.splitext(path_to_file)[1]}'

    win = tk.Toplevel(root)
    win.title("Переименование файла")
    options = ["Указ Президента", "Постановление правительства", "Федеральный закон"]
    combobox = ttk.Combobox(win, values=options)
    combobox.pack(pady=5, padx=10, side=tk.LEFT, fill=tk.X)

    label_input1 = tk.Label(win, text="Дата:")
    label_input1.pack(pady=5, padx=10, side=tk.LEFT, fill=tk.X)

    # Создаем два поля для пользовательского ввода
    # Создаем метки над полями ввода

    user_input1 = tk.Entry(win)
    user_input1.pack(pady=5, padx=10, side=tk.LEFT, fill=tk.X)
    user_input1.bind("<KeyRelease>", _on_date_entry_change)

    label_input2 = tk.Label(win, text="Номер:")
    label_input2.pack(pady=5, padx=10, side=tk.LEFT, fill=tk.X)

    # Добавляем символ "#" в поле ввода для "Название 2"
    user_input2 = tk.Entry(win)
    user_input2.pack(pady=5, padx=10, side=tk.LEFT, fill=tk.X)

    label_input3 = tk.Label(win, text="Название:")
    label_input3.pack(pady=5, padx=10, side=tk.LEFT, fill=tk.X)

    # Добавляем символ "#" в поле ввода для "Название 2"
    user_input3 = tk.Entry(win)
    user_input3.pack(pady=5, padx=10, side=tk.LEFT, fill=tk.X)
    btn_rename_files = tk.Button(win, text="Переименовать файл", command=lambda: _write_to_file(pack_name()))
    btn_rename_files.pack(pady=5, padx=10, side=tk.TOP, anchor="ne")
    preview_file(path_to_file)


def file_routine():
    global In_work, helper_window
    if not watcher.file_q.empty() and not In_work:
        helper_window = tk.Toplevel(root)
        helper_window.withdraw()
        on_new_file(watcher.file_q.get())
        In_work = True
    root.after(1000, file_routine)


def add_dir():
    def _create():
        os.mkdir(entrydir.get())
        dir_win.destroy()
        messagebox.showinfo("Создание папки", f'Успешно создано')
        show_directory_contents()

    dir_win = tk.Toplevel(root)
    labeld = tk.Label(dir_win, text="Введите название папки")
    entrydir = tk.Entry(dir_win)
    labeld.pack(pady=5, padx=10, side=tk.TOP, fill=tk.X)
    btn1 = tk.Button(dir_win, text="Создать", command=_create)
    btn1.pack(pady=5, padx=10, side=tk.BOTTOM, fill=tk.BOTH, expand=True)
    entrydir.pack(pady=5, padx=10, side=tk.BOTTOM, fill=tk.BOTH, expand=True)


root = tk.Tk()
root.title("Менеджер файлов")
style = ttk.Style(root)
style.theme_use("clam")  # Выбираем тему оформления
style.configure("Treeview", background="#f0f0f0", fieldbackground="#f0f0f0")
style.map("Treeview", background=[('selected', '#347083')])
#root.attributes("-fullscreen", True)

paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
paned_window.pack(fill=tk.BOTH, expand=True)

frame1 = tk.Frame(paned_window, bg="#f0f0f0", bd=1, relief=tk.SUNKEN)
frame1.grid(row=0, column=1, rowspan=2, sticky="nsew")
canvas = tk.Canvas(frame1, bg="#f0f0f0")
scrollbar1 = tk.Scrollbar(frame1, orient="vertical", command=canvas.yview)
scrollbar1.pack(side="right", fill="y")
scrollbar2 = tk.Scrollbar(frame1, orient="horizontal", command=canvas.xview)
scrollbar2.pack(side="bottom", fill="x")

canvas.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
canvas.bind("<MouseWheel>", on_mousewheel)
canvas.config(yscrollcommand=scrollbar1.set, xscrollcommand=scrollbar2.set)

frame2 = tk.Frame(paned_window, bg="#f0f0f0", bd=1, relief=tk.SUNKEN)
frame2.grid(row=0, column=0, sticky="nsew")

content_listbox = tk.Listbox(frame2)
content_listbox.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
content_listbox.bind("<Double-Button-1>", select_file)
content_listbox.bind("<Button-3>", show_context_menu)

frame2.grid_rowconfigure(0, weight=1)
frame2.grid_columnconfigure(0, weight=1

                            )
search_entry = tk.Entry(frame2, width=30)
search_entry.grid(row=1, column=1, sticky="ew")

search_entry.bind("<KeyRelease>", search_files)

search_label = tk.Label(frame2, text="Поиск файлов", bg="#57b0ff")
search_label.grid(row=1, column=0, padx=10, pady=10)
add_file_btn = tk.Button(frame2, text="Добавить файл", command=user_add_file)
add_file_btn.grid(row=2, column=0, padx=10, pady=10, )
add_dir_btn = tk.Button(frame2, text="Добавить папку", command=add_dir)
add_dir_btn.grid(row=2, column=1, padx=10, pady=10, )

paned_window.add(frame2)
paned_window.add(frame1)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.geometry(f'{screen_width}x{screen_height-(int(screen_height*0.1))}+0+0')

context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Переименовать", command=rename_file_from_contex)

show_directory_contents()
helper_window = tk.Toplevel(root)
helper_window.withdraw()
filename = 'directory_listing.pkl'
watcher = DirectoryWatcher(os.getcwd())
watcher.start_watching()
file_routine()

root.mainloop()