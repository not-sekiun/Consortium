import time
import os
import cfg
import modules.clear_screen as clear_screen
import modules.show_banner as show_banner

cfg.global_variables()


def cleanup():
    try:
        try:
            confirmation = raw_input('\n' + cfg.user_in + 'Are you sure you want to quit [y/n] : ')
        except EOFError:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                clear_screen.clear()
                show_banner.banner()
                return
        except KeyboardInterrupt:
            clear_screen.clear()
            return
        if confirmation == 'y':
            print cfg.shutdown
            if cfg.db_listeners:
                print cfg.note + 'Killing all active listeners...'
                cfg.db_listeners = []
                time.sleep(5)
            if cfg.db_scouts:
                try:
                    print cfg.note + 'Disconnecting all scouts...'
                    for i in cfg.db_scouts:
                        try:
                            i[5].sendall('sleep 60' + cfg.End)
                        except:
                            pass
                except IndexError:
                    print cfg.err + 'Error disconnecting scouts'
            print cfg.note + 'Exiting program...'
            os._exit(1)
        else:
            clear_screen.clear()
            show_banner.banner()
    except EOFError:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print '\n' + cfg.err + 'Skipping cleanup steps...'
            print cfg.note + 'Exiting program...'
            os._exit(1)
    except KeyboardInterrupt:
        print '\n' + cfg.err + 'Skipping cleanup steps...'
        print cfg.note + 'Exiting program...'
        os._exit(1)
