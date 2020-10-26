import library.modules.config as config

config.main()


def main():
    help_banner = '''\nScout Help Menu
===============
   Base Commands :'''
    base_help_menu = {'disconnect': 'Disconnects the scout',
                      'flush <timeout>': 'Flush the socket buffer, the socket timeout argument is optional and defaults to 5 for the socket timeout in flushing',
                      'help': 'Show the help menu or help for specific command, alias of the command is "?"',
                      'kill': 'Kills the scout',
                      'ping': 'Ping the scout',
                      'sleep': 'Make the scout disconnect and sleep for a specified amount of time'}
    longest = ''
    for i in base_help_menu:
        if len(i) > len(longest):
            longest = i
    for i in config.help_menu:
        if len(i) > len(longest):
            longest = i
    commands_base = list(base_help_menu.keys())
    commands_base.sort()
    for i in commands_base:
        help_banner += '\n      ' + i + (' ' * ((len(longest) + 3) - len(i))) + base_help_menu[i]
    commands_scout = list(config.help_menu.keys())
    commands_scout.sort()
    if commands_scout:
        help_banner += '\n\n   Scout Commands :'
        for i in commands_scout:
            help_banner += '\n      ' + i + (' ' * ((len(longest) + 3) - len(i))) + config.help_menu[i]
    help_banner += '\n'
    return help_banner
