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
            print '[*]All windows components : \n'
            for i in config.win_components:
                print i
            print '[*]All linux components : \n'
            for i in config.lin_components:
                print i
        elif to_show == 'loaded':
            print '[*]Loaded modules : '
            if config.scout_values['Windows'][0] == 'True':
                print '   windows/base_component(Default loaded module)'
            else:
                print '   linux/base_component(Default loaded module)'
            for i in config.loaded_components:
                print '   ' + i
        else:
            print '[-]Please specify a valid argument, ["options"|"components"|"loaded"]'
    except IndexError:
        print '[-]Please specify what to show, ["options"|"components"|"loaded"]'