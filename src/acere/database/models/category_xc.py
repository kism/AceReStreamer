"""Model for category xc category id."""

from sqlmodel import Field, SQLModel


class CategoryXCCategoryID(SQLModel, table=True):
    """Model for category xc category id."""

    __tablename__ = "category_xc"
    # None until the DB assigns it on insert
    xc_category_id: int | None = Field(default=None, unique=True, primary_key=True, nullable=False)
    category: str = Field(nullable=False)
