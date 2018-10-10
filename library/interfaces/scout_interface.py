import time
import library.commands.global_interface.clear as clear
import library.commands.global_interface.quit as quit
import library.commands.global_interface.python as python
import library.commands.global_interface.local as local
import library.commands.global_interface.help as help
import library.commands.scout_interface.show as show
import library.commands.scout_interface.rename as rename
import library.commands.scout_interface.more as more
import library.commands.scout_interface.kill as kill
import library.commands.scout_interface.sleep as sleep
import library.commands.scout_interface.ping as ping
import library.commands.scout_interface.disconnect as disconnect
import library.interfaces.direct_interface as direct_interface

def main():
    while True:
        try:
            prompt = raw_input('PyIris (Scouts) > ').strip()
            command = prompt.split(' ',1)[0].lower()
            if command == 'back':
                print '[*]Returning...'
                return
            elif command == 'bridge':
                stat = direct_interface.main(prompt)
                if stat == 'home':
                    return
            elif command == 'clear':
                clear.main()
            elif command == 'disconnect':
                disconnect.main(prompt)
            elif command in ('?','help'):
                help.main('scout',prompt)
            elif command == 'kill':
                kill.main(prompt)
            elif command in ('!','local'):
                local.main(prompt)
            elif command == 'rename':
                rename.main(prompt)
            elif command == 'sleep':
                sleep.main(prompt)
            elif command == 'ping':
                ping.main(prompt)
            elif command == 'python':
                python.main()
            elif command == 'quit':
                quit.main()
            elif command == 'show':
                show.main(prompt)
            elif command == 'more':
                more.main(prompt)
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