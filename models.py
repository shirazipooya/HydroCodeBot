from typing import Optional
from sqlmodel import SQLModel, Field, Session, create_engine


class User(SQLModel, table=True):
    user_id: Optional[int] = Field(primary_key=True)
    username: Optional[str]
    phone_number: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    given_name: Optional[str]
    city: Optional[str]


class Kua(SQLModel, table=True):
    user_id: Optional[int] = Field(primary_key=True)
    gender: Optional[str]
    birth_date: Optional[str]
    kua_number: Optional[str]
    count_visit: Optional[int] = 0


class Zodiac(SQLModel, table=True):
    user_id: Optional[int] = Field(primary_key=True)
    birth_date: Optional[str]
    chinese_sign: Optional[str]
    chinese_element: Optional[str]
    count_visit: Optional[int] = 0