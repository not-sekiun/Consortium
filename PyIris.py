# Version 1.1.5
import library.modules.bootstrap as bootstrap
import time
import logging

if __name__ == '__main__':
    try:
        start = bootstrap.main()
        if start:
            import library.interfaces.home_interface as home_interface
            import library.commands.global_interface.clear as clear

            clear.main()
            home_interface.main()
    except EOFError:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print('[!]User aborted bootstrap, requesting shutdown...')
            quit()
    except KeyboardInterrupt:
        print('[!]User aborted bootstrap, requesting shutdown...')
        quit()
    except Exception as e:
        logging.critical("Critical Error occurred please inform developer, dumping stack trace and exiting...", exc_info=True)
