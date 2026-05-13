from custom_socket import Client
import socket
import select
import re

IP = "127.0.0.1"
PORT = 1234

clients = set()


def parse_tagged_users(message):
    return re.findall(b"(@\\S+)", message)


def validate_username(username):
    global clients

    if " " in username:
        return False

    for client in clients:
        if client.username == username:
            return False

    return True


def send_packet(client, data: bytes):
    data_header = f"{len(data):<2048}".encode()
    client.sendall(data_header + data)


def recv_packet(client):
    try:
        data_header = client.recv(2048)

        if not data_header:
            return None

        data_length = int(data_header.decode().strip())

        total_data = b""

        while len(total_data) < data_length:
            chunk = client.recv(data_length - len(total_data))

            if not chunk:
                return None

            total_data += chunk

        return total_data

    except:
        return None


def notify_clients(user, status):
    global clients

    for client in clients:
        data = (
            f"{user.username} s {status}"
        ).encode()

        client.send_buff.put(data)


def send_online_users(new_user):
    global clients

    for online_user in clients:
        data = (
            f"{online_user.username} s 1"
        ).encode()

        new_user.send_buff.put(data)


def get_username(client):
    data = recv_packet(client)

    if data is None:
        return False

    username = data.decode().strip()

    if not validate_username(username):
        send_packet(client, b"1")
        print(f"bad username from {client.ip}")
        return False

    client.username = username

    send_packet(client, b"0")

    print(f"{client.ip} is called {username}")

    return True


def handle_new_connection(server):
    global clients

    client, addr = server.accept()

    client.setblocking(False)

    client.ip = addr[0]

    print(f"{addr} connected")

    success = get_username(client)

    if not success:
        client.close()
        return

    notify_clients(client, 1)

    send_online_users(client)

    clients.add(client)


def broadcast_message(sender, message):
    global clients

    tagged_users = parse_tagged_users(message)

    if tagged_users:
        print(f"{sender.username} tagged {tagged_users}")

    for receiver in clients:

        should_send = (
            not tagged_users
            or b"@" + receiver.username.encode() in tagged_users
            or receiver == sender
        )

        if should_send:

            data = (
                f"[{sender.ip}] {sender.username}: "
            ).encode() + message

            receiver.send_buff.put(data)


def handle_receiver(receiver):
    while not receiver.send_buff.empty():

        try:
            data = receiver.send_buff.get()
            send_packet(receiver, data)

        except Exception as e:
            print("send failed:", e)


def disconnect_client(client):
    global clients

    print(f"{client.ip} disconnected")

    if client in clients:
        clients.remove(client)

    notify_clients(client, 0)

    client.close()


server = Client(socket.AF_INET, socket.SOCK_STREAM)

server.setblocking(False)

server.bind((IP, PORT))

server.listen()

print(f"server listening on {IP}:{PORT}")

while True:

    readable, _, broken_clients = select.select(
        clients | {server},
        [],
        clients
    )

    for sock in readable:

        if sock == server:

            handle_new_connection(server)

        else:

            data = recv_packet(sock)

            if data is None:
                broken_clients.append(sock)
                continue

            message = data.decode().strip()

            print(f"{sock.username}: {message}")

            if message == "/exit":
                broken_clients.append(sock)
                continue

            broadcast_message(sock, data)

    for broken_socket in broken_clients:
        disconnect_client(broken_socket)

    for receiver in clients:
        if not receiver.send_buff.empty():
            handle_receiver(receiver)
