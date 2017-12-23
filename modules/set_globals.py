import modules.cfg as cfg
import validate_ip as validate_ip

cfg.global_variables()

def set_global_variables(command):
    try:
        action = command.split(' ')[0]
        type_of_list = command.split(' ')[1]
        ip_addr = command.split(' ')[2]
        if validate_ip.validate_ip_str(ip_addr):
            if action == 'add':
                if type_of_list == 'wlist':
                    cfg.whitelisted_ip.append(ip_addr)
                    print cfg.pos + 'Added to whitelist'
                elif type_of_list == 'blist':
                    cfg.blacklisted_ip.append(ip_addr)
                    print cfg.pos + 'Added to blacklist'
                else:
                    raise IndexError
            elif action == 'rm':
                try:
                    if type_of_list == 'wlist':
                        cfg.whitelisted_ip.remove(ip_addr)
                        print cfg.pos + 'Removed from whitelist'
                    elif type_of_list == 'blist':
                        cfg.blacklisted_ip.remove(ip_addr)
                        print cfg.pos + 'Removed from blacklist'
                    else:
                        raise IndexError
                except ValueError:
                    print cfg.err + 'Value not in whitelist or blacklist'
            else:
                raise IndexError
        else:
            print cfg.err + 'Invalid IP address'
    except IndexError:
        print cfg.err + 'Invalid command syntax/command arguments'