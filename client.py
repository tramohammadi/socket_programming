import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime

IP = "127.0.0.1"
PORT = 1234
ADDRESS = (IP, PORT)

stop_event = threading.Event()


def send_packet(sock, data: bytes):
    header = f"{len(data):<2048}".encode()
    sock.sendall(header + data)


def recv_packet(sock):
    header = sock.recv(2048)

    if not header:
        return None

    length = int(header.decode().strip())

    data = b""

    while len(data) < length:
        chunk = sock.recv(length - len(data))

        if not chunk:
            return None

        data += chunk

    return data


class ChatGUI:
    def __init__(self, sock, username):
        self.sock = sock
        self.username = username

        # ---- Main Window ----
        self.root = tk.Tk()
        self.root.title(f"Chat - {username}")
        self.root.geometry("750x500")

        # ---- Main Frame (Split Layout) ----
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Chat area (Left)
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Users list (Right)
        right_frame = tk.Frame(main_frame, width=200)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # Chat messages
        self.chat_area = scrolledtext.ScrolledText(left_frame)
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        self.chat_area.config(state="disabled")

        # Message entry
        bottom_frame = tk.Frame(left_frame)
        bottom_frame.pack(fill=tk.X)
        self.entry = tk.Entry(bottom_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.entry.bind("<Return>", self.send_message)

        self.send_btn = tk.Button(bottom_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.exit_btn = tk.Button(bottom_frame, text="Exit", command=self.on_close)
        self.exit_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Online users part
        self.users_label = tk.Label(right_frame, text="Online Users:", font=("Arial", 11, "bold"))
        self.users_label.pack(anchor="nw")

        self.users_list = tk.Listbox(right_frame)
        self.users_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Thread to receive messages
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def add_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.chat_area.config(state="disabled")
        self.chat_area.yview(tk.END)

    def send_message(self, event=None):
        message = self.entry.get().strip()
        if not message:
            return
        try:
            send_packet(self.sock, message.encode())
        except Exception as e:
            self.add_message(f"send failed: {e}")
        self.entry.delete(0, tk.END)

    def receive_messages(self):
        while not stop_event.is_set():
            try:
                data = recv_packet(self.sock)
                if data is None:
                    self.add_message("Server disconnected.")
                    stop_event.set()
                    break
                message = data.decode()
                if message.startswith("USERS:"):
                    self.update_users(message)
                else:
                    self.add_message(message)
            except Exception as e:
                self.add_message(f"Receive error: {e}")
                stop_event.set()
                break

        try:
            self.sock.close()
        except:
            pass

    def update_users(self, message):
        users = message.replace("USERS:", "").split(",")
        self.users_list.delete(0, tk.END)
        for user in users:
            if user.strip():
                self.users_list.insert(tk.END, user)

    def on_close(self):
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            try:
                send_packet(self.sock, b"/exit")
            except:
                pass
            stop_event.set()
            try:
                self.sock.close()
            except:
                pass
            self.root.destroy()

    def run(self):
        self.root.mainloop()

class LoginGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login - Chat App")
        self.root.geometry("300x180")

        tk.Label(self.root, text="Enter Username:", font=("Arial", 12)).pack(pady=10)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)
        self.username_entry.bind("<Return>", self.connect)

        self.connect_btn = tk.Button(self.root, text="Connect", command=self.connect)
        self.connect_btn.pack(pady=10)

        self.status_label = tk.Label(self.root, text="", fg="red")
        self.status_label.pack()

    def connect(self, event=None):
        username = self.username_entry.get().strip()
        if not username:
            self.status_label.config(text="Username cannot be empty.")
            return

        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_sock.connect(ADDRESS)
        except Exception as e:
            self.status_label.config(text=f"Connection failed: {e}")
            return

        send_packet(client_sock, username.encode())
        response = recv_packet(client_sock)
        if not response:
            self.status_label.config(text="Server error.")
            client_sock.close()
            return

        code = response.decode()
        if code == "0":
            self.root.destroy()
            chat_gui = ChatGUI(client_sock, username)
            chat_gui.run()
        elif code == "1":
            self.status_label.config(text="Username taken or invalid.")
            client_sock.close()
        else:
            self.status_label.config(text="Unknown server response.")
            client_sock.close()


def main():
    login = LoginGUI()
    login.root.mainloop()


if __name__ == "__main__":
    main()
