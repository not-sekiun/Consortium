import library.modules.config as config

config.main()


def main(data, context_type='components', operation='load'):
    print len(config.win_components)
    print config.win_components
    try:
        data = data.replace(' ', '')
        if data == 'all':  # filter special phrase
            if context_type == 'components' and operation == 'load':  # filter special context
                if config.scout_values['Windows'][0] == 'True':
                    return [str(i) for i in config.win_components.keys() if
                            not config.win_components[str(i)].startswith('windows/bases/')]
                else:
                    return [str(i) for i in config.lin_components.keys() if
                            not config.lin_components[str(i)].startswith('linux/bases/')]
            elif data == 'all' and operation == 'unload':
                return ['all']
            elif context_type == 'encoders' and operation == 'load':
                return config.encoders.keys()
        try:  # only ints seperated with ","
            id_storage = data.split(',')
            id_storage = map(int, id_storage)
            for i in id_storage:
                try:  # check for "-" in comma values
                    if '-' in str(i):
                        ranges = i.split('-', 1)
                        tmp_data = range(int(ranges[0]) + int(ranges[1]))
                        id_storage += tmp_data
                except (ValueError, IndexError):
                    print config.err
            return list(set(id_storage))
        except (ValueError, IndexError):  # no commas check for singular value
            try:
                id_storage = int(data)
                return [id_storage]
            except (ValueError, IndexError):
                try:  # check for singular range
                    ranges = data.split('-')
                    list_of_ids = range(int(ranges[0]), int(ranges[1]) + 1)
                    return list(set(list_of_ids))
                except (ValueError, IndexError):  # check for combination of both
                    list_of_ids = []
                    ranges = data.split(',')
                    for i in ranges:
                        if '-' in i:
                            i = i.split('-')
                            cache_list_of_ids = range(int(i[0]), int(i[1]) + 1)
                            list_of_ids += cache_list_of_ids
                        else:
                            list_of_ids.append(int(i))
                    return list(set(list_of_ids))
    except OverflowError:
        print config.war + 'Values out of range (Are you trying to break my ID system?)'
        return []
    except:
        return [data]
