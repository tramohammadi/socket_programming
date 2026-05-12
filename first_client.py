import socket

HOST = '127.0.0.1'
PORT = 8080

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect((HOST, PORT))
print(f'Connected to server {HOST}:{PORT}')

message = "Hello server!"
client_socket.sendall(message.encode("utf-8"))

try:
    data = client_socket.recv(1024)

    if data:
        print("Server response:", data.decode("utf-8"))

except ConnectionResetError:
    print("Server connection lost")

client_socket.close()
print("Connection closed")
