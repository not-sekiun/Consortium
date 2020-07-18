import socket


def main(sock, sock_timeout=None):
    sock.settimeout(sock_timeout)
    try:
        data = sock.recv(1000000)
        if not data:
            return '' #no data received
        processed_data = data.decode()  # Only test for encoding in the first part just so we can take out length bytes if we can .decode() the first segment it doesnt guarantee future segments can be .decoded()
        target_length = int(processed_data.split("|",1)[0])  # length of message
        data = data[len(str(target_length))+1:]  # usable data
    except UnicodeDecodeError:
        target_length = int(data.decode(encoding='utf-8', errors='ignore').split("|",1)[0])
        data = data[len(str(target_length))+1:]  # usable data minus the indicator and length bytes

    received_data_length = len(data) # actual received length of usable data we got excluding length of size bytes and seperator
    if received_data_length >= target_length: # x|data where value x denotes only length of data we take away the bytes that were unaccounted for namely length of x + 1 (the seperator)
        try:
            return data.decode()  # text data
        except UnicodeDecodeError:
            return data  # binary data

    sock.settimeout(3)  # NOTE we disregard byte encoding when obtaining data we only decode at the very end when we have all data we cannot decode and assume for each individual segment
    while received_data_length < target_length:  # we now no longer have to account for the free bytes used at the front but must account for the used bytes should they have been insufficient
        try:
            tmp_data = sock.recv(1000000)
            if not tmp_data:
                raise socket.error
            data += tmp_data
            received_data_length += 1000000
        except (socket.error, socket.timeout):  # in case of network hiccup/ network error disconnect we bail out
            break
    try:
        return data.decode()  # text data
    except UnicodeDecodeError:
        return data  # binary data
