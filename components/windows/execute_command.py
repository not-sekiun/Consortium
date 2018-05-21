import library.modules.config as config

config.main()

def main(option):
    if option == 'generate':
        print 'NIL'
    elif option == 'info':
        print '\nName             : Execute command component' \
              '\nOS               : Windows' \
              '\nRequired Modules : subprocess' \
              '\nCommands         : exec' \
              '\nDescription      : A remote shell command execution component of the scout, it allows the scout to remotely execute commands\n'