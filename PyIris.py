import sys

if __name__ == '__main__':
    if sys.version_info < (3, 0):
        try:
            from colorama import init
            from modules.config_checker import *
            from modules.main_handler import *
        except IndentationError:#ImportError:
            print '[-]modules folder has been tampered, reinstall from github'
            exit()
        init()
        test()
        root_console()
    else:
        print ('[-]Run in python 2.X')