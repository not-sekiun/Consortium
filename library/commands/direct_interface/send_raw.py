import socket
import library.modules.config as config

config.main()


def main(scout_id,command):
    try:
        command = command.split(' ',1)[1]
        config.scout_database[scout_id][0].sendall(command)
        data = config.scout_database[scout_id][0].recv(999999)
        print data
    except (IndexError, KeyError):
        print '[-]Please enter a valid scout ID'
        return
    except socket.error:
        print '[-]Scout is dead, removing from database...'
        del(config.scout_database[scout_id])