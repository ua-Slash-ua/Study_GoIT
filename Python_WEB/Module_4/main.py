import mimetypes
import urllib.parse
import json
import logging
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
from threading import Thread

BASE_DIR = Path("front-init")
BUFFER_SIZE = 1024
http_port = 3000
http_host = "0.0.0.0"
socket_host = "127.0.0.1"
socket_port = 4000


# Додайте цю функцію
def initialize_storage():
    # Шлях до каталогу storage
    storage_dir = Path("front-init/storage")

    # Створіть каталог, якщо він не існує
    if not storage_dir.exists():
        logging.info("Creating storage directory.")
        storage_dir.mkdir(parents=True)

    # Шлях до файлу data.json
    data_file = storage_dir / "data.json"

    # Створіть файл, якщо він не існує
    if not data_file.exists():
        logging.info("Creating data.json file.")
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump({}, f)  # Заповнюємо файл порожнім JSON об'єктом


class HomeFramework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html("front-init/index.html")
            case "/message.html":
                self.send_html("front-init/message.html")
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("front-init/error.html")

    def do_POST(self):
        size = self.headers.get("Content-Length")
        data = self.rfile.read(int(size))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (socket_host, socket_port))
        self.send_response(302)
        self.send_header("Location", "message.html")
        self.end_headers()

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_types, *_ = mimetypes.guess_type(filename)
        if mime_types:
            self.send_header("Content-Type", mime_types)
        else:
            self.send_header("Content-Type", "text/plain")
        self.end_headers()
        with open(filename, "rb") as f:
            self.wfile.write(f.read())


def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    try:

        parse_dict = {
            f"{datetime.now()}": {
                key: value
                for key, value in [el.split("=") for el in parse_data.split("&")]
            }
        }
        with open("front-init/storage/data.json", "w", encoding="utf-8") as file:
            json.dump(parse_dict, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP сокет
    server_socket.bind((host, port))
    logging.info("Starting socket srever")
    try:
        while True:
            # Отримуємо повідомлення від клієнта
            message, client_address = server_socket.recvfrom(BUFFER_SIZE)
            save_data_from_form(message)
    except KeyboardInterrupt:
        server_socket.close()


def run_http_server(host, post):
    adress = (host, post)
    http_server = HTTPServer(adress, HomeFramework)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


if __name__ == "__main__":
    initialize_storage()

    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s %(message)s")
    server = Thread(target=run_http_server, args=(http_host, http_port))
    server.start()
    server_socket = Thread(target=run_socket_server, args=(socket_host, socket_port))
    server_socket.start()
