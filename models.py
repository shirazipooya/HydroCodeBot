from typing import Optional
from sqlmodel import SQLModel, Field, Session, create_engine


class Kua(SQLModel, table=True):
    user_id: Optional[int] = Field(primary_key=True)
    first_name: Optional[str]
    last_name: Optional[str]
    gender: Optional[str]
    birth_date: Optional[str]
    kua_number: Optional[str]