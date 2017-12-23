import pickle
import socket
import threading
import cfg
import modules.thread_kill as thread_kill


cfg.global_variables()

def start_listener(ip, port, listener_key, fake_reply):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((ip, port))
        s.listen(1)
        cfg.distributed_listener_id += 1
        local_handler_id = cfg.distributed_listener_id
        cfg.db_listeners.append([local_handler_id, ip , str(port), listener_key])
        print cfg.pos + 'Started listener at : ' + ip + ':' + str(port)
        while True:
            if not thread_kill.kill_listener_thread(str(local_handler_id)):
                try:
                    s.settimeout(3)
                    conn, addr = s.accept()
                    conn.setblocking(1)
                except (socket.timeout,socket.error):
                    continue
                if conn:
                    server_patrol_check = addr[0]
                    if cfg.whitelisted_ip:
                        if server_patrol_check not in cfg.whitelisted_ip:
                            conn.shutdown(1)
                            conn.close()
                            continue
                    if cfg.blacklisted_ip:
                        if server_patrol_check in cfg.blacklisted_ip:
                            conn.shutdown(1)
                            conn.close()
                            continue
                    try:
                        conn.settimeout(5)
                        scout_info = pickle.loads(conn.recv(9999999))
                    except (socket.error, socket.timeout):
                        conn.sendall(fake_reply)
                        conn.shutdown(1)
                        conn.close()
                        continue
                    try:
                        if scout_info[0] == cfg.scout_key:
                            if scout_info[1] == listener_key:
                                scout_info.pop(0)
                                cfg.scouts_id += 1
                                scout_info[0] = cfg.scouts_id
                                scout_info.insert(1, addr[0])
                                scout_info.append(conn)
                            else:
                                conn.send('sleep 60' + cfg.End)
                                buffer_out_reply = conn.recv(99999)
                                continue
                        else:
                            conn.sendall(fake_reply)
                            conn.shutdown(1)
                            conn.close()
                            continue
                        cfg.db_scouts.append(scout_info)
                        print '\n' + cfg.pos + 'Scout with Identifying name : ' + scout_info[2] + ' has reported back'
                    except IndexError:
                        conn.sendall(cfg.fake_reply)
                        conn.shutdown(1)
                        conn.close()
                        continue
                else:
                    conn.shutdown(1)
                    conn.close()
            else:
                cfg.screenlock.acquire()
                print cfg.note + 'Killing listener at : ' + ip + ':' + str(port)
                s.close()
                print cfg.pos + 'Killed listener succesfully'
                cfg.screenlock.release()
                return
    except Exception as e:
        print cfg.err + 'Error from listener : ' + str(e)
        print cfg.note + 'Killing listener in error state...'
        try:
            for i in range(len(cfg.db_listeners)):
                if cfg.db_listeners[i][0] == local_handler_id:
                    cfg.db_listeners.pop(i)
        except:
            pass
        print cfg.pos + 'Killed listener succesfully'
        return
