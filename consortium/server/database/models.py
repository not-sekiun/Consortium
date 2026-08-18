import uuid
from datetime import datetime

from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RepositoryResourceORM(Base):
    resource_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str]
    datetime_created: Mapped[datetime]
    is_directory: Mapped[bool]


class AssetORM(RepositoryResourceORM):
    __tablename__ = "assets"
    user_account_username: Mapped[str]
    user_account_role: Mapped[str]


class ArtifactORM(RepositoryResourceORM):
    __tablename__ = "artifacts"
    agent_id: Mapped[uuid.UUID]
    agent_name: Mapped[str]
    agent_type: Mapped[str]


class PayloadORM(RepositoryResourceORM):
    __tablename__ = "payloads"

    agent_template_label: Mapped[str]
    agent_template_name: Mapped[str]
    build_parameters: Mapped[JSON]
    payload_data: Mapped[JSON]
