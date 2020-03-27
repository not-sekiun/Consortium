import socket


def main(sock, data):
    try: # normal utf-8 message that needs to be byte encoded
        sock.sendall((str(len(data)) + "|" + data).encode())
    except TypeError: # raw bytes that are technically alr encoded
        sock.sendall(str(len(data)).encode() + b"|" + data)
