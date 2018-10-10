import collections


def main(dictionary):
    tmp_dict = collections.OrderedDict()
    try:
        tmp_list = dictionary.keys()
        tmp_list.remove('-')
        for i in sorted(map(int, tmp_list)):
            tmp_dict[str(i)] = dictionary[str(i)]
        tmp_dict['-'] = dictionary['-']
        return tmp_dict
    except TypeError:
        return dictionary
