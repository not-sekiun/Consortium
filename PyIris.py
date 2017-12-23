import sys

if __name__ == '__main__':
    if sys.version_info < (3, 0):
        try:
            import os
            if not os.path.isfile('persistent_creds.txt'):
                print '[-]Run set_creds.py in sub-folder setup'
                os._exit(1)
            f = open('persistent_creds.txt','r')
            test_empty_string = f.read().split('\n')
            if len(test_empty_string) < 3:
                print '[-]Run set_creds.py in sub-folder setup'
                os._exit(1)
            from colorama import init
            import modules.config_checker as config_checker
            import handlers.main_handler as main_handler
            init()
            config_checker.test()
            main_handler.main_handler_console()
        except ImportError:
            print '[-]modules folder has been tampered with, please reinstall'
            exit()
    else:
        print ('[-]Run in python 2.X')