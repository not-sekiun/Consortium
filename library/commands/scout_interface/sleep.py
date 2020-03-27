import socket
import library.modules.config as config
import library.modules.send_all as send_all
import library.modules.recv_all as recv_all

config.main()


def main(scout_id):
    try:
        slp_scout_id = scout_id.split(' ', 2)[1]
        sleep_dur = scout_id.split(' ', 2)[2]
        if slp_scout_id == 'all':
            for i in list(config.scout_database.keys()):
                try:
                    print(config.inf + 'Sleeping scout of ID : ' + i)
                    send_all.main(config.scout_database[i][0],'sleep ' + sleep_dur)
                    data = recv_all.main(config.scout_database[i][0])
                    print(data)
                    del (config.scout_database[i])
                except socket.error:
                    print(config.neg + 'Scout is dead, removing from database...')
                    del (config.scout_database[i])
        else:
            send_all.main(config.scout_database[slp_scout_id][0], 'sleep ' + sleep_dur)
            data = recv_all.main(config.scout_database[slp_scout_id][0])
            print(data)
            del (config.scout_database[slp_scout_id])
    except KeyError:
        print(config.neg + 'Please enter a valid scout ID')
        return
    except IndexError:
        print(config.neg + 'Please enter valid arguments')
    except socket.error:
        print(config.neg + 'Scout is dead, removing from database...')
        del (config.scout_database[scout_id])
