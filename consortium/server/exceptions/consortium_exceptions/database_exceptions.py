class EntryNotFoundError(Exception):
    def __init__(self, entry_id: str):
        self.entry_id = entry_id
        super().__init__(
            f"Failed to get entry. Entry with entry ID '{entry_id}' was not found."
        )
