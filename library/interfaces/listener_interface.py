import time
import library.commands.global_interface.clear as clear
import library.commands.global_interface.quit as quit
import library.commands.global_interface.python as python
import library.commands.global_interface.local as local
import library.commands.global_interface.help as help
import library.commands.listener_interface.show as show
import library.commands.listener_interface.set as set
import library.commands.listener_interface.run as run
import library.commands.listener_interface.kill as kill
import library.commands.listener_interface.more as more
import library.commands.listener_interface.reset as reset
import library.commands.listener_interface.rename as rename
import library.modules.socket_connector as socket_connector
import library.modules.config as config

try:
    import readline
except ImportError:
    import gnureadline as readline

config.main()
listener_commands = ['clear', 'help', 'local', 'python', 'quit', 'bind', 'kill', 'more', 'rename', 'reset', 'run',
                     'set', 'show',
                     'back']


def listener_completer(text, state):
    for cmd in listener_commands:
        if cmd.startswith(text):
            if not state:
                return cmd
            else:
                state -= 1


def main():
    readline.parse_and_bind("tab: complete")
    readline.set_completer(listener_completer)
    while True:
        try:
            prompt = input(
                '\x1b[1m\x1b[37mPyIris (\x1b[0m' + '\x1b[1m\x1b[34mListeners\x1b[0m' + '\x1b[1m\x1b[37m) > \x1b[0m').strip()
            command = prompt.split(' ', 1)[0].lower()
            if command == 'back':
                print(config.inf + 'Returning...')
                return
            elif command == 'bind':
                print(config.inf + 'Binding...')
                socket_connector.main(prompt)
            elif command == 'clear':
                clear.main()
            elif command in ('?', 'help'):
                help.main('listener', prompt)
            elif command == 'kill':
                kill.main(prompt)
            elif command in ('!', 'local'):
                local.main(prompt)
            elif command == 'more':
                more.main(prompt)
            elif command == 'python':
                python.main()
            elif command == 'quit':
                quit.main()
            elif command == 'rename':
                rename.main(prompt)
            elif command == 'reset':
                reset.main(prompt)
            elif command == 'run':
                run.main()
            elif command == 'show':
                show.main(prompt)
            elif command == 'set':
                set.main(prompt)
            elif not command:
                pass
            else:
                print(config.neg + 'Invalid command, run "help" for help menu')
        except KeyboardInterrupt:
            quit.main()
