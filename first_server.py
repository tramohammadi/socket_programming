import socket

HOST = '127.0.0.1'
PORT = 8080

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind((HOST, PORT))
server_socket.listen(5)

print(f'Server is listening on {HOST}:{PORT}')

while True:
    client_socket, client_address = server_socket.accept()
    print(f'Accepted connection from {client_address}')

    while True:
        try:
            data = client_socket.recv(1024)

            if not data:
                break

            message = data.decode("utf-8")
            print(f'Client says: {message}')

            response = "Hello client!"
            client_socket.sendall(response.encode("utf-8"))

        except ConnectionResetError:
            print("Client disconnected unexpectedly")
            break

    client_socket.close()
    print(f'Connection with {client_address} closed')
