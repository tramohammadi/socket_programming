import socket
import threading
import sys

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


def receive_messages(sock):
    while not stop_event.is_set():

        try:
            data = recv_packet(sock)

            if data is None:
                print("server disconnected")
                stop_event.set()
                break

            print(data.decode())

        except Exception as e:
            if not stop_event.is_set():
                print("receive failed:", e)
            stop_event.set()
            break

    try:
        sock.close()
    except:
        pass


def read_input(sock):
    while not stop_event.is_set():

        try:
            message = input()

            if message == "/exit":

                try:
                    send_packet(sock, message.encode())
                except:
                    pass

                stop_event.set()
                break

            send_packet(sock, message.encode())

        except EOFError:
            stop_event.set()
            break


def connect():

    while True:

        username = input("enter username: ").strip()

        if not username:
            continue

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            client.connect(ADDRESS)
        except Exception as e:
            print("connection failed:", e)
            continue

        send_packet(client, username.encode())

        response = recv_packet(client)

        if response is None:
            print("server error")
            client.close()
            continue

        response = response.decode()

        if response == "0":
            print("connected to server")
            return client

        elif response == "1":
            print("username already taken or invalid")
            client.close()

        else:
            print("unknown server response")
            client.close()


def main():

    client = connect()

    recv_thread = threading.Thread(
        target=receive_messages,
        args=(client,),
        daemon=True
    )

    input_thread = threading.Thread(
        target=read_input,
        args=(client,),
        daemon=True
    )

    recv_thread.start()
    input_thread.start()

    recv_thread.join()
    input_thread.join()

    try:
        client.close()
    except:
        pass

    print("client closed")
    sys.exit(0)


if __name__ == "__main__":
    main()
