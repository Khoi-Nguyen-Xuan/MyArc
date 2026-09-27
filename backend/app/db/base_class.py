from sqlalchemy.orm import declarative_base

# Single declarative base shared by every model. Kept in its own module
# (no other imports) so models can import it without circular-import
# issues; app/db/base.py is the one that imports both this and every
# model, for Alembic's autogenerate to see the full metadata.
Base = declarative_base()
