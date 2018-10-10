import time
import library.commands.global_interface.clear as clear
import library.commands.global_interface.quit as quit
import library.commands.global_interface.python as python
import library.commands.global_interface.local as local
import library.commands.global_interface.help as help
import library.commands.home_interface.regen as regen
import library.commands.home_interface.add as add
import library.commands.home_interface.show as show
import library.commands.home_interface.rm as rm
import library.commands.home_interface.reset as reset
import library.interfaces.listener_interface as listener_interface
import library.interfaces.scout_interface as scout_interface
import library.interfaces.generator_interface as generator_interface

def main():
    while True:
        try:
            prompt = raw_input('PyIris (Home) > ').strip()
            command = prompt.split(' ',1)[0].lower()
            if command == 'add':
                add.main(prompt)
            elif command == 'clear':
                clear.main()
            elif command == 'generator':
                print '[*]Switching...'
                generator_interface.main()
            elif command in ('?','help'):
                help.main('home',prompt)
            elif command == 'listeners':
                print '[*]Switching...'
                listener_interface.main()
            elif command in ('!' ,'local'):
                local.main(prompt)
            elif command == 'python':
                python.main()
            elif command == 'quit':
                quit.main()
            elif command == 'regen':
                regen.main()
            elif command == 'reset':
                reset.main(prompt)
            elif command == 'rm':
                rm.main(prompt)
            elif command == 'scouts':
                print '[*]Switching...'
                scout_interface.main()
            elif command == 'show':
                show.main(prompt)
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