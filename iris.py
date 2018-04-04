#Version 0.6.2
import library.modules.bootstrap as bootstrap
import time

if __name__ == '__main__':
    try:
        start = bootstrap.main()
        if start:
            time.sleep(3)
            import library.interfaces.home_interface as home_interface
            import library.commands.global_interface.clear as clear
            clear.main()
            home_interface.main()
    except IndexError:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print '[!]User aborted bootstrap, requesting shutdown...'
            quit()
    except KeyboardInterrupt:
        print '[!]User aborted bootstrap, requesting shutdown...'
        quit()