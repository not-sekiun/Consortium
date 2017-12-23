import cfg, socket

cfg.global_variables()

End = cfg.End

def recvall(tar_socket):
    tar_socket.settimeout(None)
    data = tar_socket.recv(9999)
    if not data:
        return ''
    while True:
        if data.endswith(End):
            try:
                tar_socket.settimeout(1)
                more_data = tar_socket.recv(9999)
                if not more_data:
                    return data[:-len(End)].replace('[+]', cfg.pos, 1).replace('[-]', cfg.err, 1).replace('[*]',cfg.note, 1)
                data += more_data
            except (socket.timeout,socket.error):
                tar_socket.settimeout(None)
                return data[:-len(End)].replace('[+]',cfg.pos,1).replace('[-]',cfg.err,1).replace('[*]',cfg.note,1)
        else:
            more_data = tar_socket.recv(9999)
            data += more_data