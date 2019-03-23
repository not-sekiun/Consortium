import library.modules.return_random_string as return_random_string
import library.modules.config as config
import socket
from datetime import datetime

config.main()


def main(args):
    try:
        host = args.split(' ')[1]
        port = int(args.split(' ')[2])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((host, port))
        print config.pos + 'Established a bind TCP connection to ' + host + ':' + str(port)
        if config.white_list:
            if host not in config.white_list:
                s.close()
                print config.neg + 'Connection was aborted because host was not in whitelist'
                return
        elif config.black_list:
            if host in config.black_list:
                s.close()
                print config.neg + 'Connection was aborted because host was in blacklist'
                return
        s.settimeout(5)
        try:
            await_key = s.recv(9999999)
        except (socket.timeout, socket.error):
            print config.neg + 'Established connection to ' + host + ':' + str(port) + ' but no data received!'
            return
        s.settimeout(None)
        if await_key == config.key:
            print config.pos + 'Key from scout matches, connection is allowed'
            config.scout_database[str(config.incremented_scout_id)] = [s, host, str(port),
                                                                       host + ':' + str(port),
                                                                       return_random_string.main(5),
                                                                       datetime.now().strftime(
                                                                           '%Y-%m-%d %H:%M:%S'),
                                                                       'Bind']
            print config.inf + 'Entry added to database'
            config.incremented_scout_id += 1
        else:
            print config.neg + 'Invalid key was supplied from scout, denying connection...'
            s.close()
    except (socket.timeout, socket.error):
       print config.neg + 'Unable to establish bind TCP connection to ' + host + ':' + str(port)
    except (IndexError, ValueError):
        print config.neg + 'Please specify a valid hostname and port number'
