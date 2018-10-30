import os
import library.modules.config as config

config.main()


def main():
    try:
        print config.inf + 'Opening python interpreter on local system'
        os.system('python')
    except KeyboardInterrupt:
        pass
    print config.inf + 'Exiting...'
