import re
import library.modules.config as config

config.main()


def main(inp_data, context_type, operation):
    data = inp_data.replace(' ', '')
    if data == 'all':  # filter special cases
        if context_type == 'components' and operation == 'load':
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

    # Actual formatting occurs here

    error = False
    output_list = []  # final list of individual sorted values
    ranges = []  # ranges to process later
    non_ranges = []
    data = inp_data.split(',')  # split by comma
    data = list(set(data))  # remove all duplicates after comma split

    for i in data:
        if re.match('^[0-9]+\-[0-9]+$',
                    i):  # initialize regex match to format of range IDs, matches "positive number-positive"
            ranges.append(i)
        else:
            non_ranges.append(i)
    # process non ranges first
    for i in non_ranges:
        try:
            output_list.append(int(i))
        except:
            error = True  # indicate formatting error
            break
    if error and output_list:  # we hit an error however we still hit a match indicating invalid format
        print 'Invalid generator ID formatting : String detected while sorting for integer IDs'
        return
    elif error and not output_list and not ranges:  # nothing in non ranges is an integer and there are no proper ranges meaning string based input only
        print config.neg + 'Generator found no IDs'
        if type(inp_data) is list:
            return inp_data
        return [inp_data]  # most probably a direct call for the component which we return

    # ERROR OUTPUT_LIST BOOLEAN CHEATSHEET
    # error and non zero output_list TT -> indicates that in non range some are ints others are not which is invalid formatting
    # no error and zero output_list FF -> not possible due to the nature of try: except, one or the other happens
    # error and zero output_list TF -> indicates that nothing in non ranges is an integer meaning string only or range only formatting
    # no error and non zero output_list FT -> indicates that everything in non ranges is integer

    # iterate range values to add to output
    try:
        for i in ranges:
            f_val, s_val = i.split('-', 1)
            # even if f_val and s_val are non zero numbers that start with digit 0, INTing them normalizes it
            f_val = int(f_val)
            s_val = int(s_val)
            # f_val and s_val are never negative since regex matches "positive number-positive number"
            if f_val > s_val:
                print config.neg + 'Invalid generator ID formatting : First range value is larger than second range value'
                return
            else:  # 0 < f < s
                mini_range = range(f_val, s_val + 1)  # add 1 to account for the final val
                output_list += mini_range  # fill each value in range of f and s into output
    except OverflowError:
        print config.neg + 'Invalid generator ID formatting : Range value is too large'
        return []

    output_list = list(set(output_list))  # remove all duplicates in the range addition section ^
    output_list.sort()  # sort for better eyecandy when loading components
    print config.pos + 'Generator ID formatting successful'
    if type(output_list) is list:
        return output_list
    return [output_list] # final function iterates through output
