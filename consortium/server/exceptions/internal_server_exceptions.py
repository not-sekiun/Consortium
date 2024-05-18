# Internal exceptions for the agent profiles service. These do not inherit
# from ServerException because they should not be handled by the server exception
# handlers
class InvalidAgentProjectManifestFileError(Exception):
    pass


class InvalidAgentProjectFolderStructureError(Exception):
    pass


class InvalidAgentProjectSymbolError(Exception):
    pass


class InvalidAgentProjectImplementationError(Exception):
    pass


class InternalAgentProjectError(Exception):
    pass


# Internal exceptions for the listener profiles service. These do not inherit
# from ServerException because they should not be handled by the server exception
# handlers
class InvalidListenerProjectManifestFileError(Exception):
    pass


class InvalidListenerProjectFolderStructureError(Exception):
    pass


class InvalidListenerProjectSymbolError(Exception):
    pass


class InvalidListenerProjectImplementationError(Exception):
    pass


class InternalListenerProjectError(Exception):
    pass


# Internal exceptions for the plugins service. These do not inherit from
# ServerException because they should not be handled by the server exception handlers
class InvalidPluginProjectManifestFileError(Exception):
    pass


class InvalidPluginProjectFolderStructureError(Exception):
    pass


class InvalidPluginProjectSymbolError(Exception):
    pass


class InvalidPluginProjectImplementationError(Exception):
    pass


class InternalPluginProjectError(Exception):
    pass


# Internal exceptions for the event hooks service. These do not inherit from
# ServerException because they should not be handled by the server exception handlers
class InvalidEventHookProjectManifestFileError(Exception):
    pass


class InvalidEventHookProjectFolderStructureError(Exception):
    pass


class InvalidEventHookProjectSymbolError(Exception):
    pass


class InvalidEventHookProjectImplementationError(Exception):
    pass


class InternalEventHookProjectError(Exception):
    pass


# Internal exceptions for the user accounts service. These do not inherit from
# ServerException because they should not be handled by the server exception handlers
class InvalidUserAccountError(Exception):
    pass


class DuplicateUserAccountUsernamesError(Exception):
    pass


class UserAccountsFileNotFoundError(Exception):
    pass


class InvalidUserAccountsFileError(Exception):
    pass
