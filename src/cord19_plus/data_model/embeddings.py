from typing import List
from typing import Optional

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Table, Column, Integer, String, Float, ARRAY
from sqlalchemy import ForeignKey


from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy import JSON


Base = declarative_base()


class Embedding(Base):

    __tablename__ = "embedding"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    docno: Mapped[str] = mapped_column(String(1024), nullable=False)  # String with a length of 1024
    embedding: Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=False)