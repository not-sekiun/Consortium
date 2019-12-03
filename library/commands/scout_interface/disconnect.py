import socket
import library.modules.config as config

config.main()


def main(scout_id):
    try:
        scout_id = scout_id.split(' ', 1)[1]
        if scout_id == 'all':
            for i in list(config.scout_database.keys()):
                try:
                    print(config.inf + 'Disconnecting scout of ID : ' + i)
                    config.scout_database[i][0].sendall('disconnect'.encode())
                    data = config.scout_database[i][0].recv(999999).decode()
                    print(data)
                    del (config.scout_database[i])
                except socket.error:
                    print(config.neg + 'Scout is dead, removing from database...')
                    del (config.scout_database[i])
        else:
            config.scout_database[scout_id][0].sendall('disconnect'.encode())
            data = config.scout_database[scout_id][0].recv(999999).decode()
            print(data)
            del (config.scout_database[scout_id])
    except (IndexError, KeyError):
        print(config.neg + 'Please enter a valid scout ID')
        return
    except socket.error:
        print(config.neg + 'Scout is dead, removing from database...')
        del (config.scout_database[scout_id])
