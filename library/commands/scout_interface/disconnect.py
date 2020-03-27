import socket
import library.modules.config as config
import library.modules.send_all as send_all
import library.modules.recv_all as recv_all

config.main()


def main(scout_id):
    try:
        scout_id = scout_id.split(' ', 1)[1]
        if scout_id == 'all':
            for i in list(config.scout_database.keys()):
                try:
                    print(config.inf + 'Disconnecting scout of ID : ' + i)
                    send_all.main(config.scout_database[i][0], 'disconnect')
                    data = recv_all.main(config.scout_database[i][0])
                    print(data)
                    del (config.scout_database[i])
                except socket.error:
                    print(config.neg + 'Scout is dead, removing from database...')
                    del (config.scout_database[i])
        else:
            send_all.main(config.scout_database[scout_id][0], 'disconnect')
            data = recv_all.main(config.scout_database[scout_id][0])
            print(data)
            del (config.scout_database[scout_id])
    except (IndexError, KeyError):
        print(config.neg + 'Please enter a valid scout ID')
        return
    except socket.error:
        print(config.neg + 'Scout is dead, removing from database...')
        del (config.scout_database[scout_id])
