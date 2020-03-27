import os
import time
import socket
import threading
import library.modules.config as config
import library.modules.send_all as send_all
import library.modules.recv_all as recv_all

config.main()


def main():
    try:
        confirm_exit = input('\n' + config.pro + 'Are you sure you want to exit[y/n] : ')
        if confirm_exit == 'y':
            print(config.inf + 'User requested shutdown...')
            if config.listener_database:
                print(config.lod + 'Killing all active listeners')
                print(config.inf + 'Sent kill message to all listeners...')
                print(config.inf + 'Waiting for response...')
                config.listener_database = {}
                while threading.active_count() > 1:
                    continue
                print(config.pos + 'Done')
            if config.scout_database:
                print(config.lod + 'Disconnecting all scouts')
                for i in config.scout_database:
                    try:
                        send_all.main(config.scout_database[i][0], 'disconnect')
                        config.scout_database[i][0].settimeout(5)
                        buffer_out_reply = recv_all.main(config.scout_database[i][0])
                        config.scout_database[i][0].close()
                        print(config.pos + 'Closed connection to scout of ID : ' + i)
                    except (socket.error, socket.timeout):
                        print(config.neg + 'Could not close connection to scout of ID : ' + i)
                        pass
                print(config.pos + 'Done')
            print(config.pos + 'Exiting...')
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
