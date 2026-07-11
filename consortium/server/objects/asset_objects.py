from typing import TYPE_CHECKING

from pydantic import JsonValue

from consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions import (
    UserAccountUsernameNotFoundError,
)
from consortium.server.models.user_account_models import LiveUserAccountReferenceModel
from consortium.server.objects.repository_objects import (
    RepositoryDirectory,
    RepositoryFile,
)

if TYPE_CHECKING:
    from consortium.server.services.user_accounts_service import UserAccountsService


class Asset:
    """A view over a repository resource that adds live uploading-account resolution.

    An asset wraps a "dumb" repository file or directory together with the user accounts
    service so that, on demand, the account that uploaded the asset can be resolved to
    its current live representation. The wrapped resource stores only an immutable
    point-in-time reference to the uploading account (its ID and username at the moment
    of upload); the referenced account may later be renamed or deleted. Resolution is
    therefore always optional and additive: it never mutates the stored reference and a
    missing account never invalidates the asset.

    Attribute access that is not defined on the asset itself is delegated to the wrapped
    repository resource, so an asset can be treated like the file or directory it wraps.
    """

    def __init__(
        self,
        resource: RepositoryFile | RepositoryDirectory,
        user_accounts_service: UserAccountsService,
    ):
        self._resource = resource
        # Held so the uploading account reference recorded on the wrapped resource can be
        # resolved to a live account on demand via the `resolved_user_account` property.
        self._user_accounts_service = user_accounts_service

    def __getattr__(self, name: str):
        # Only invoked when normal attribute lookup on the asset fails. Delegates to the
        # wrapped resource so callers and the REST API can reach resource attributes
        # (path, name, is_directory, resource_id, read, etc.) directly on the asset.
        # Guard `_resource` so a lookup before it is set cannot recurse infinitely.
        if name == "_resource":
            raise AttributeError(name)
        return getattr(self._resource, name)

    def __str__(self) -> str:
        return f"Asset({self._resource})"

    def __repr__(self) -> str:
        return (
            f"Asset("
            f"resource={self._resource!r}, "
            f"user_accounts_service={self._user_accounts_service!r}"
            f")"
        )

    @property
    def resolved_user_account(self) -> LiveUserAccountReferenceModel | None:
        """The live account that uploaded this asset, or `None` if it cannot be resolved.

        Resolves the uploading account reference stored on the asset to its current
        representation by querying the user accounts service. Returns `None` when the
        asset records no uploading account, or when the referenced account no longer
        exists (for example it was deleted after the asset was created). This is a live,
        additive lookup: it never mutates the stored reference.
        """
        user_account_reference = self._resource.data.get("user_account")
        if not user_account_reference:
            return None
        username = user_account_reference.get("username")
        if username is None:
            return None
        try:
            user_account = self._user_accounts_service.get_user_account_by_username(
                username=username,
            )
        except UserAccountUsernameNotFoundError:
            return None
        return LiveUserAccountReferenceModel(
            user_account_id=user_account.user_account_id,
            username=user_account.username,
            role=user_account.role,
        )

    def to_json(
        self, include_checksum: bool = False, force_checksum_refresh: bool = False
    ) -> dict[str, JsonValue]:
        """Serializes the asset, augmenting `data` with the resolved uploading account.

        Produces the wrapped resource's JSON representation and, within its `data` field,
        adds a `resolved_user_account` key holding the live uploading account (or `None`
        when it cannot be resolved). The stored `data` is copied rather than mutated, so
        the resolved view never leaks into what the repository persists to disk.
        """
        resource_json = self._resource.to_json(
            include_checksum=include_checksum,
            force_checksum_refresh=force_checksum_refresh,
        )
        resolved_user_account = self.resolved_user_account
        resource_json["data"] = {
            **resource_json["data"],
            "resolved_user_account": resolved_user_account.model_dump(mode="json")
            if resolved_user_account is not None
            else None,
        }
        return resource_json
