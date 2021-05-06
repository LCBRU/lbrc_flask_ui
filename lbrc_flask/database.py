import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


db = SQLAlchemy()


# See https://docs.sqlalchemy.org/en/13/core/custom_types.html#backend-agnostic-guid-type
class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

def dialect_date_format_string(format_string):
    if db.session.bind.dialect.name == 'sqlite':
        return format_string.replace('%b', '%m')
    elif db.session.bind.dialect.name == 'mysql':
        return format_string


def dialect_format_date(field, format_string):
    if db.session.bind.dialect.name == 'sqlite':
        return func.strftime(format_string, field)
    elif db.session.bind.dialect.name == 'mysql':
        return func.date_format(field, format_string)


