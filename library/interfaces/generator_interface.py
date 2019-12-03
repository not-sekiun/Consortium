import time
import library.modules.generator_append as generator_append
import library.commands.global_interface.clear as clear
import library.commands.global_interface.quit as quit
import library.commands.global_interface.python as python
import library.commands.global_interface.local as local
import library.commands.global_interface.help as help
import library.commands.generator_interface.show as show
import library.commands.generator_interface.reset as reset
import library.commands.generator_interface.set as set
import library.commands.generator_interface.load_com as load_com
import library.commands.generator_interface.unload_com as unload_com
import library.commands.generator_interface.generate as generate
import library.commands.generator_interface.more_com as more_com
import library.commands.generator_interface.load_enc as load_enc
import library.commands.generator_interface.unload_enc as unload_enc
import library.commands.generator_interface.more_enc as more_enc
import library.modules.config as config

try:
    import readline
except ImportError:
    import gnureadline as readline


config.main()
generator_commands = ['clear', 'help', 'local', 'python', 'quit', 'generate', 'load_com', 'unload_com', 'load_enc',
                      'unload_enc', 'more_com', 'more_enc', 'reset', 'set', 'show', 'back']


def generator_completer(text, state):
    for cmd in generator_commands:
        if cmd.startswith(text):
            if not state:
                return cmd
            else:
                state -= 1


def main():
    readline.parse_and_bind("tab: complete")
    readline.set_completer(generator_completer)
    while True:
        try:
            generator_append.main()
            prompt = input(config.generator_prompt).strip()
            command = prompt.split(' ', 1)[0].lower()
            if command == 'back':
                print(config.inf + 'Returning...')
                return
            elif command == 'clear':
                clear.main()
            elif command == 'generate':
                generate.main()
            elif command in ('?', 'help'):
                help.main('generator', prompt)
            elif command == 'load_com':
                load_com.main(prompt)
            elif command == 'load_enc':
                load_enc.main(prompt)
            elif command in ('!', 'local'):
                local.main(prompt)
            elif command == 'more_com':
                more_com.main(prompt)
            elif command == 'more_enc':
                more_enc.main(prompt)
            elif command == 'python':
                python.main()
            elif command == 'quit':
                quit.main()
            elif command == 'reset':
                reset.main(prompt)
            elif command == 'set':
                set.main(prompt)
            elif command == 'show':
                show.main(prompt)
            elif command == 'unload_com':
                unload_com.main(prompt)
            elif command == 'unload_enc':
                unload_enc.main(prompt)
            elif not command:
                pass
            else:
                print(config.neg + 'Invalid command, run "help" for help menu')
        except EOFError:
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                quit.main()
        except KeyboardInterrupt:
            quit.main()
