import library.modules.config as config

config.main()


def main(command):
    try:
        to_show = command.split(' ', 1)[1]
        if to_show == 'options':
            header = [['    Option', 'Value', 'Info'], ['    ======', '=====', '====']]
            for o, v in config.listener_values.items():
                header.append(['    ' + o, str(v[0]), v[1]])
            print('\n')
            l = [len(max(i, key=len)) for i in zip(*header)]
            print('\n'.join('     '.join(item[i].ljust(l[i]) for i in range(len(l)))
                            for item in header) + '\n')
        elif to_show == 'listeners':
            header = [['    ID', 'Name', 'Socket Address'],
                      ['    ==', '====', '==============']]
            tmp_list = []
            for i in config.listener_database:
                tmp_list.append([i, config.listener_database[i][2],
                                 config.listener_database[i][0] + ':' + str(config.listener_database[i][1])])
            tmp_list.sort()
            for i in tmp_list:
                header.append(['    ' + i[0], i[1], i[2]])
            l = [len(max(i, key=len)) for i in zip(*header)]
            print('\n')
            print('\n'.join('     '.join(item[i].ljust(l[i]) for i in range(len(l)))
                            for item in header) + '\n')
        else:
            print(config.neg + 'Please specify a valid argument, ["options"|"listeners"]')
    except IndexError:
        print(config.neg + 'Please specify what to show, ["options"|"listeners"]')
