import library.modules.config as config

config.main()

def main(id):
    if id in config.listener_database.keys():
        return False
    else:
        return True