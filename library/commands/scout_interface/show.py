import library.modules.config as config

config.main()

def main(command):
    try:
        to_show = command.split(' ',1)[1]
        if to_show == 'scouts':
            header = [['    ID', 'Name', '[Scout] -> [Listener]'],
                      ['    ==', '====', '=====================']]
            tmp_list = []
            for i in config.scout_database:
                tmp_list.append([i, config.scout_database[i][4], config.scout_database[i][1] + ':' + config.scout_database[i][2] + ' -> ' + config.scout_database[i][3]])
            tmp_list.sort()
            for i in tmp_list:
                header.append(['    ' + str(i[0]),i[1],i[2]])
            l = [len(max(i, key=len)) for i in zip(*header)]
            print '\n'
            print('\n'.join('     '.join(item[i].ljust(l[i]) for i in range(len(l)))
                            for item in header)) + '\n'
        else:
            print config.neg + 'Please specify a valid argument, ["scouts"]'
    except IndexError:
        print config.neg + 'Please specify what to show, ["scouts"]'