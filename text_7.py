from customtkinter import *
from websocket import WebSocketApp
import threading
import time

BLOCK_FIELDS = ["fuck", "die", "$"]
EMOJI = {
    "axe": "🪓",
    "lol": "-__-",
    "ok": "❤️"
}


class LoginWindow(CTk):
    def __init__(self):
        super().__init__()
        self.username = None
        self.geometry('400x200')
        self.title("Вхід у чат")

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.label = CTkLabel(self, text="Введіть ваше ім'я:", font=('Arial', 14, 'bold'))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 0))

        self.username_entry = CTkEntry(self, placeholder_text="Ім'я користувача", width=200, height=40)
        self.username_entry.grid(row=1, column=0, padx=20, pady=(0, 20))
        self.username_entry.bind("<Return>", self.login)

        self.login_button = CTkButton(self, text='Увійти', width=100, height=40, command=self.login)
        self.login_button.grid(row=2, column=0, padx=20, pady=(0, 20))

    def login(self, event=None):
        username = self.username_entry.get()
        if username and username.isalpha() and username.isascii():
            self.username = username
            self.destroy()
        else:
            self.label.configure(text="Ім'я може містити тільки англійські літери!")


class MainWindow(CTk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.label = None
        self.ws = None
        self.ws_connected = False
        self.last_msg_ts = time.time()
        self.block_fields = ["fuck", "die", "$"]

        self.geometry('600x400')
        self.title(f"Чат - {self.username}")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.chat_field = CTkTextbox(self, font=('Arial', 14, 'bold'), state='disable')
        self.chat_field.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.message_entry = CTkEntry(self, placeholder_text='Введіть повідомлення:', height=40)
        self.message_entry.grid(row=1, column=0, sticky="ew")
        self.message_entry.bind("<Return>", self.send_message)

        self.send_button = CTkButton(self, text='>', width=50, height=40, command=self.send_message)
        self.send_button.grid(row=1, column=1, sticky="e")

        self.connect_to_server()

    def connect_to_server(self):
        def on_message(ws, message):
            self.add_message(message)

        def on_error(ws, error):
            self.add_message(f"Помилка: {error}")

        def on_close(ws, close_status_code, close_msg):
            self.ws_connected = False
            self.add_message("[СЕРВЕР] З'єднання з сервером закрито")
            time.sleep(5)
            self.connect_to_server()

        def on_open(ws):
            self.ws_connected = True
            self.add_message("[СЕРВЕР] З'єднання з сервером встановлено")

        def run_websocket():
            self.ws = WebSocketApp(
                f"ws://107.161.154.244:9779/logika/ws/{self.username}",
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            self.ws.run_forever()

        threading.Thread(target=run_websocket, daemon=True).start()

    def add_message(self, text):
        fix_text = text
        for field in BLOCK_FIELDS:
            lower_text = fix_text.lower()
            lower_field = field.lower()
            if lower_field in lower_text:
                start = 0
                while True:
                    index = lower_text.find(lower_field, start)
                    if index == -1:
                        break
                    fix_text = fix_text[:index] + ('* ' * len(field)) + fix_text[index + len(field):]
                    lower_text = fix_text.lower()
                    start = index + len(field)



        def update_chat():
            self.chat_field.configure(state='normal')
            self.chat_field.insert(END, fix_text + '\n')
            self.chat_field.see(END)
            self.chat_field.configure(state='disable')

        if threading.current_thread() != threading.main_thread():
            self.after(0, update_chat)
        else:
            update_chat()

    def send_message(self, event=None):
        message = self.message_entry.get()

        now_ts = time.time()
        if now_ts - self.last_msg_ts < 1:
            self.add_message("Не СПАМ!")
            self.message_entry.delete(0, END)
        else:
            self.last_msg_ts = now_ts

            message = message.strip()
            fields = message.split(":")
            message_final = ""
            for field in fields:
                if field in EMOJI:
                    message_final += EMOJI[field]
                else:
                    message_final += field

            if message_final and self.ws_connected:
                self.ws.send(message_final)
                self.message_entry.delete(0, END)
            elif message_final:
                self.add_message("Не вдалося надіслати повідомлення: немає з'єднання з сервером")
                self.message_entry.delete(0, END)

login_window = LoginWindow()
login_window.mainloop()

if login_window.username:
    win = MainWindow(login_window.username)
    win.mainloop()