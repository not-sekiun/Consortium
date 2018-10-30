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
import library.modules.config as config

config.main()


def main():
    while True:
        try:
            prompt = raw_input(
                '\x1b[1m\x1b[37mPyIris (\x1b[0m\033[94mListeners\033[1m\033[0m\x1b[1m\x1b[37m) > \x1b[0m').strip()
            command = prompt.split(' ', 1)[0].lower()
            if command == 'back':
                print config.inf + 'Returning...'
                return
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
                print config.neg + 'Invalid command, run "help" for help menu'
        except EOFError:
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                quit.main()
        except KeyboardInterrupt:
            quit.main()
