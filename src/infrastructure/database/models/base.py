from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr

from src.core.config import settings
from src.core.utils import convert_model_class_to_table_name


class Base(DeclarativeBase):
    __abstract__ = True

    metadata = MetaData(naming_convention=settings.db.naming_convention)

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        return f"{convert_model_class_to_table_name(cls.__name__)}"
