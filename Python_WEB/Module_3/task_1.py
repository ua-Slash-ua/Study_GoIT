from pathlib import Path
from threading import Thread
import shutil


def copy_file(path_input: str, path_output: str = "dist", name=None):

    Path(path_output).mkdir(exist_ok=True)
    output_path = Path(path_output)
    extension = Path(name).suffix
    same_extension_files = [f for f in output_path.iterdir() if f.suffix == extension]

    if same_extension_files:
        shutil.copy(path_input, output_path / name)
        print(f"Файл {name} скопійовано до {path_output}")
    else:
        new_dir = output_path / extension[1:]
        new_dir.mkdir(exist_ok=True)
        shutil.copy(path_input, new_dir / name)
        print(f"Файл {name} скопійовано до {new_dir}")


def check_directory_contents(path_input: str, path_output: str = "dist"):
    # Створюємо об'єкт шляху
    p = Path(path_input)

    if any(p.iterdir()):
        for element in p.iterdir():
            if element.is_file():
                th_copy = Thread(
                    target=copy_file,
                    args=(f"{path_input}/{element.name}", path_output, element.name),
                )
                th_copy.start()
            elif element.is_dir():

                th = Thread(
                    target=check_directory_contents,
                    args=(f"{path_input}/{element.name}", path_output),
                )
                th.start()
    else:
        print("Папка порожня.")


check_directory_contents(
    "picture",
)
