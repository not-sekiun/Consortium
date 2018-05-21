import library.modules.config as config

config.main()

def main(command):
    try:
        to_show = command.split(' ',1)[1]
        if to_show == 'options':
            header = [['    Option', 'Value', 'Info'], ['    ======', '=====', '====']]
            for o, v in config.scout_values.items():
                header.append(['    ' + o, str(v[0]), v[1]])
            print '\n'
            l = [len(max(i, key=len)) for i in zip(*header)]
            print('\n'.join('     '.join(item[i].ljust(l[i]) for i in range(len(l)))
                            for item in header)) + '\n'
        elif to_show == 'components':
            print '\n[*]All loadable windows components :'
            for i in config.win_components:
                print i
            print '\n'
            print '[*]All loadable linux components :'
            for i in config.lin_components:
                print i
            print '\n'
        elif to_show == 'loaded':
            print '[*]Loaded modules : '
            for i in config.loaded_components:
                print '   ' + i
        else:
            print '[-]Please specify a valid argument, ["options"|"components"|"loaded"]'
    except IndexError:
        print '[-]Please specify what to show, ["options"|"components"|"loaded"]'