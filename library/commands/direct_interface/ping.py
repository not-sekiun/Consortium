import socket
import library.modules.config as config

config.main()


def main(scout_id):
    try:
        config.scout_database[scout_id][0].sendall('ping')
        data = config.scout_database[scout_id][0].recv(999999)
        print data
        return True
    except socket.error:
        print config.neg + 'Scout is dead, removing from database...'
        del (config.scout_database[scout_id])
        return False