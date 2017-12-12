import socket, pickle, cfg
from modules.thread_kill import *

cfg.global_variables()


def start_listening(port):
    try:
        s = socket.socket()
        s.bind(('0.0.0.0', port))
        s.listen(100)
        cfg.listeners_id += 1
        local_id = cfg.listeners_id
        cfg.db_listeners.append([local_id, str(port)])
        print cfg.pos + 'Listener started and bound to port : ' + str(port)
        while True:
            if kill_listener_thread(str(local_id)):
                try:
                    s.settimeout(3)
                    c, a = s.accept()
                except socket.timeout:
                    continue
                if c:
                    if cfg.whitelisted_ip:
                        if a[0] in cfg.whitelisted_ip:
                            pass
                        else:
                            c.shutdown(1)
                            c.close()
                            continue
                    if cfg.blacklisted_ip:
                        if a[0] in cfg.blacklisted_ip:
                            c.shutdown(1)
                            c.close()
                            continue
                        else:
                            pass
                    try:
                        c.setblocking(1)
                        scouts_info = pickle.loads(c.recv(9999999))
                    except:
                        c.shutdown(1)
                        c.close()
                        continue
                    if scouts_info[0] == cfg.key:
                        cfg.scouts_id += 1
                        scouts_info[0] = cfg.scouts_id
                        ip_addr = a[0]
                        scouts_info.insert(1, ip_addr)
                        scouts_info.append(c)
                    else:
                        c.shutdown(1)
                        c.close()
                    cfg.db_scouts.append(scouts_info)
                    print '\n' + cfg.pos + 'Scout with assigned name : '+scouts_info[2]+' has reported back'
                else:
                    c.close()
                    continue
            else:
                s.close()
                return
    except Exception as e:
        print '\n' + cfg.err + 'Error from listener : ' + str(e)
        print '\n' + cfg.note + 'Killing failed listener thread...'
        try:
            for i in range(len(cfg.db_listeners)):
                if cfg.db_listeners[i][0] == local_id:
                    cfg.db_listeners.pop(i)
        except:
            pass
        return
