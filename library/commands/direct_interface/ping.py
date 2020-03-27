import socket
import library.modules.config as config
import library.modules.send_all as send_all
import library.modules.recv_all as recv_all

config.main()


def main(scout_id):
    try:
        send_all.main(config.scout_database[scout_id][0], 'ping')
        data = recv_all.main(config.scout_database[scout_id][0])
        print(data)
        return True
    except socket.error:
        print(config.neg + 'Scout is dead, removing from database...')
        del (config.scout_database[scout_id])
        return False
