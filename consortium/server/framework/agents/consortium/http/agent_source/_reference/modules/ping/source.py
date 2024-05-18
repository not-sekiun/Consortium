class ModuleSource:
    def __init__(self):
        pass

    def run_module(self, command, args, connection):
        connection.send_string("[+] Agent is alive!")
