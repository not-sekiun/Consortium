class ModuleSource:
    def run_module(self, _arguments, connection):
        connection.send_string("[+] Agent is alive!")
