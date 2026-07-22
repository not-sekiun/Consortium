class NotAPlugin:
    # compatible_framework_version must exist so the version check is skipped and the
    # interface check (issubclass) is what raises ComponentInterfaceError.
    compatible_framework_version = None
