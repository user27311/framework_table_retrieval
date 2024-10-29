from typing import List
from typing import Optional

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Table, Column, Integer, String, Float, ARRAY
from sqlalchemy import ForeignKey


from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy import JSON


Base = declarative_base()

class GoldTable(Base):

    __tablename__ = "gold_table"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ir_id: Mapped[str] = mapped_column(String(1024))
    ir_tab_id: Mapped[str] = mapped_column(String(1024))

    content: Mapped[str] = mapped_column(String(2**15), nullable=True) #32768
    content_json: Mapped[JSON] = mapped_column(type_=JSON, nullable=False)

    position_page: Mapped[int] = mapped_column(Integer(), nullable=True) #do we want to map this to document pages?
    position_left: Mapped[float] = mapped_column(Float(), nullable=True)
    position_top: Mapped[float] = mapped_column(Float(), nullable=True)
    width: Mapped[float] = mapped_column(Float(), nullable=True)
    height: Mapped[float] = mapped_column(Float(), nullable=True)

    caption: Mapped[str] = mapped_column(String(2**15), nullable=True)
    references: Mapped[List[str]] = mapped_column(ARRAY(String(2**15)), nullable=True)

    relevance_label: Mapped[int] = mapped_column(Integer(), nullable=True)
    annotator_name: Mapped[str] = mapped_column(String(1024), nullable=True)
    