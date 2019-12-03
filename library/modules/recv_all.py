import socket


def main(sock):
    encode = True
    sock.settimeout(None)
    try:
        data = sock.recv(999999)
        data = data.decode()
    except UnicodeDecodeError:
        encode = False
    sock.settimeout(5)
    while True:
        try:
            if encode:
                tmp_data = sock.recv(999999).decode()
            else:
                tmp_data = sock.recv(999999)
            if not tmp_data:
                raise socket.error
            data += tmp_data
        except (socket.error, socket.timeout):
            return data
