import socket
import library.modules.config as config
import library.modules.recv_all as recv_all

config.main()


def main(scout_id, timeout=5):
    bytes_flushed = 0
    while True:
        try:
            data = recv_all.main(config.scout_database[scout_id][0], timeout)
            if len(data) == 0:
                break
            bytes_flushed += len(data)
        except (socket.error, socket.timeout):
            break
    print(config.pos + 'Flushed ' + str(bytes_flushed) + ' bytes from scout socket')
