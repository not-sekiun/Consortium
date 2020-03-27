import library.modules.config as config
import library.modules.recv_all as recv_all
import library.modules.send_all as send_all

config.main()


def main(data, scout_id):
    send_all.main(config.scout_database[scout_id][0], data)
    data = recv_all.main(config.scout_database[scout_id][0])
    return data
