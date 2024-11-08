class ModuleSource:
    def run_module(self, connection, arguments):
        yield {"success": True, "message": "Agent is alive.", "data": {}}
