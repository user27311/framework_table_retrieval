from typing import List
from typing import Optional

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Table, Column, Integer, String, Float, ARRAY
from sqlalchemy import ForeignKey


from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase


Base_Meta = declarative_base()


class MetaData(Base_Meta):
    __tablename__ = "MetaData"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cord_uid: Mapped[str] = mapped_column(String(128))
    sha: Mapped[str] = mapped_column(String(2**17), nullable=True)
    source_x: Mapped[str] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(2**17), nullable=True)
    doi: Mapped[str] = mapped_column(String(128), nullable=True)
    pmcid: Mapped[str] = mapped_column(String(128), nullable=True)
    pubmed_id: Mapped[str] = mapped_column(String(128), nullable=True)
    license: Mapped[str] = mapped_column(String(128), nullable=True)
    abstract: Mapped[str] = mapped_column(String(2**17), nullable=True)
    publish_time: Mapped[str] = mapped_column(String(128), nullable=True)
    authors: Mapped[str] = mapped_column(String(2**17), nullable=True)
    journal: Mapped[str] = mapped_column(String(1024), nullable=True)
    mag_id: Mapped[str] = mapped_column(String(128), nullable=True)
    who_covidence_id: Mapped[str] = mapped_column(String(128), nullable=True)
    arxiv_id: Mapped[str] = mapped_column(String(128), nullable=True)
    pdf_json_files: Mapped[str] = mapped_column(String(2**17), nullable=True)
    pmc_json_files: Mapped[str] = mapped_column(String(2**17), nullable=True)
    url: Mapped[str] = mapped_column(String(2**17), nullable=True)
    s2_id: Mapped[str] = mapped_column(String(128), nullable=True)

