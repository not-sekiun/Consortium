import threading
import time
import library.modules.config as config
import library.modules.socket_listener as socket_listener

config.main()

def main():
    try:
        host = config.listener_values['Interface'][0]
        port = int(config.listener_values['Port'][0])
        name = config.listener_values['Name'][0]
        t = threading.Thread(target=socket_listener.main,
                             args=(host, port, name))
        t.start()
        time.sleep(3)
    except (IndexError, ValueError):
        print '[-]Please use valid values'