import socket
import library.modules.config as config

config.main()

def main(scout_id):
    try:
        scout_id = scout_id.split(' ',1)[1]
        if scout_id == 'all':
            for i in config.scout_database.keys():
                try:
                    print '[*]Pinging scout of ID : ' + i
                    config.scout_database[i][0].sendall('ping')
                    data = config.scout_database[i][0].recv(999999)
                    print data
                except socket.error:
                    print '[-]Scout is dead, removing from database...'
                    del (config.scout_database[i])
        else:
            config.scout_database[scout_id][0].sendall('ping')
            data = config.scout_database[scout_id][0].recv(999999)
            print data
    except (IndexError, KeyError):
        print '[-]Please enter a valid scout ID'
        return
    except socket.error:
        print '[-]Scout is dead, removing from database...'
        del(config.scout_database[scout_id])