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
import library.commands.generator_interface.load as load
import library.commands.generator_interface.unload as unload
import library.commands.generator_interface.generate as generate
import library.commands.generator_interface.more as more


def main():
    while True:
        try:
            generator_append.main()
            prompt = raw_input('PyIris (Generator) > ').strip()
            command = prompt.split(' ',1)[0]
            if command == 'back':
                print '[*]Returning...'
                return
            elif command == 'clear':
                clear.main()
            elif command == 'generate':
                generate.main()
            elif command in ('?','help'):
                help.main('generator',prompt)
            elif command == 'load':
                load.main(prompt)
            elif command in ('!' ,'local'):
                local.main(prompt)
            elif command == 'more':
                more.main(prompt)
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
            elif command == 'unload':
                unload.main(prompt)
            elif not command:
                pass
            else:
                print '[-]Invalid command, run "help" for help menu'
        except EOFError:
            try:
                time.sleep(2)
            except KeyboardInterrupt:
                quit.main()
        except KeyboardInterrupt:
            quit.main()