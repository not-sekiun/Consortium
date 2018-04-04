import os
import time
import socket
import threading
import library.modules.config as config

config.main()


def main():
    try:
        confirm_exit = raw_input('\n[>]Are you sure you want to exit[y/n] : ')
        if confirm_exit == 'y':
                print '[*]User requested shutdown...'
                if config.listener_database:
                    print '[...]Killing all active listeners'
                    print '[*]Sent kill message to all listeners...'
                    print '[*]Waiting for response...'
                    config.listener_database = {}
                    while threading.active_count() > 1:
                        continue
                    print '[+]Done'
                if config.scout_database:
                    print '[...]Disconnecting all scouts'
                    for i in config.scout_database:
                        try:
                            config.scout_database[i][0].send('disconnect')
                            config.scout_database[i][0].settimeout(5)
                            buffer_out_reply = config.scout_database[i][0].recv(999999999)
                            config.scout_database[i][0].close()
                            print '[+]Closed connection to scout of ID : ' + i
                        except (socket.error, socket.timeout):
                            print '[-]Could not close connection to scout of ID : ' + i
                            pass
                    print '[+]Done'
                print '[+]Exiting...'
                os._exit(1)
        else:
            pass
    except EOFError:
        try:
            time.sleep(2)
            quit()
        except KeyboardInterrupt:
            quit()
    except KeyboardInterrupt:
        quit()