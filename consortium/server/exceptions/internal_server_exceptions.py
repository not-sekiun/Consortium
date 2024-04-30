# Internal exceptions for the agent templates service. These do not inherit
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


# Internal exceptions for the listener templates service. These do not inherit
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
