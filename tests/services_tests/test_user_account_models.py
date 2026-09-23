from consortium.server.models.user_account_models import (
    PersistentUserAccountModel,
    UserAccountModel,
)

# The password field is marked repr=False so that reprs of an account (and of anything
# that reprs one, such as a User) never leak the plaintext password into logs.


def test_user_account_model_repr_omits_password():
    model = UserAccountModel(
        username="operator",
        password="super-secret-password",
        role="admin",
    )

    representation = repr(model)

    assert "super-secret-password" not in representation
    assert "operator" in representation


def test_persistent_user_account_model_repr_omits_password():
    model = PersistentUserAccountModel(
        username="operator",
        password="super-secret-password",
        role="admin",
    )

    representation = repr(model)

    assert "super-secret-password" not in representation
    assert "operator" in representation
