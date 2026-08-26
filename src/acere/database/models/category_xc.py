"""Model for category xc category id."""

from sqlmodel import Field, SQLModel


class CategoryXCCategoryID(SQLModel, table=True):
    """Model for category xc category id."""

    __tablename__ = "category_xc"
    xc_category_id: int = Field(unique=True, primary_key=True, nullable=False)
    category: str = Field(nullable=False)
