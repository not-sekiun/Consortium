import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RepositoryResourceDBModel(Base):
    __abstract__ = True

    resource_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str]
    datetime_created: Mapped[datetime]
    is_directory: Mapped[bool]


class AssetDBModel(RepositoryResourceDBModel):
    __tablename__ = "assets"

    user_account_username: Mapped[str]
    user_account_role: Mapped[str]


class ArtifactDBModel(RepositoryResourceDBModel):
    __tablename__ = "artifacts"

    agent_id: Mapped[uuid.UUID]
    agent_name: Mapped[str]
    agent_type: Mapped[str]


class PayloadDBModel(RepositoryResourceDBModel):
    __tablename__ = "payloads"

    agent_template_label: Mapped[str]
    agent_template_name: Mapped[str]
    build_parameters: Mapped[dict[str, Any]] = mapped_column(JSON)
    payload_data: Mapped[dict[str, Any]] = mapped_column(JSON)
