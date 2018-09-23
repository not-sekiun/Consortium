import library.modules.config as config
import library.modules.recv_all as recv_all

config.main()

def main(data,scout_id):
    print config.scout_database
    config.scout_database[scout_id][0].sendall(data)
    data = recv_all.main(config.scout_database[scout_id][0])
    return data