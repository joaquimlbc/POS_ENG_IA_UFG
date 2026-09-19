"""SQLAlchemy ORM models for REST Countries API domain entities.

This module defines the database schema using SQLAlchemy 2.0 with type hints,
relationships, and constraints aligned with the PRD specifications.
"""

from datetime import datetime
from typing import List

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


class Country(Base):
    """Country entity representing a nation with geographic and demographic data.

    Relationships:
        languages: One-to-many with Language
        currencies: One-to-many with Currency
        timezones: One-to-many with Timezone
    """

    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_common: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name_official: Mapped[str] = mapped_column(String(255), nullable=False)
    iso_code_2: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    iso_code_3: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subregion: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    population: Mapped[int] = mapped_column(BigInteger, nullable=False)
    area: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    languages: Mapped[List["Language"]] = relationship(
        back_populates="country", cascade="all, delete-orphan", lazy="selectin"
    )
    currencies: Mapped[List["Currency"]] = relationship(
        back_populates="country", cascade="all, delete-orphan", lazy="selectin"
    )
    timezones: Mapped[List["Timezone"]] = relationship(
        back_populates="country", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_iso_code_2", "iso_code_2"),
        Index("idx_iso_code_3", "iso_code_3"),
        Index("idx_region", "region"),
        Index("idx_region_subregion", "region", "subregion"),
    )

    def __repr__(self) -> str:
        return (
            f"<Country(id={self.id}, name={self.name_common}, iso2={self.iso_code_2})>"
        )


class Language(Base):
    """Language entity representing languages spoken in a country.

    Relationships:
        country: Many-to-one with Country
    """

    __tablename__ = "country_languages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    country_id: Mapped[int] = mapped_column(
        ForeignKey("countries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language_code: Mapped[str] = mapped_column(String(10), nullable=False)
    language_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship
    country: Mapped["Country"] = relationship(back_populates="languages")

    __table_args__ = (Index("idx_language_country", "country_id"),)

    def __repr__(self) -> str:
        return f"<Language(id={self.id}, code={self.language_code}, name={self.language_name})>"


class Currency(Base):
    """Currency entity representing currencies used in a country.

    Relationships:
        country: Many-to-one with Country
    """

    __tablename__ = "country_currencies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    country_id: Mapped[int] = mapped_column(
        ForeignKey("countries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    currency_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship
    country: Mapped["Country"] = relationship(back_populates="currencies")

    __table_args__ = (Index("idx_currency_country", "country_id"),)

    def __repr__(self) -> str:
        return f"<Currency(id={self.id}, code={self.currency_code}, name={self.currency_name})>"


class Timezone(Base):
    """Timezone entity representing timezones in a country.

    Relationships:
        country: Many-to-one with Country
    """

    __tablename__ = "country_timezones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    country_id: Mapped[int] = mapped_column(
        ForeignKey("countries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timezone_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship
    country: Mapped["Country"] = relationship(back_populates="timezones")

    __table_args__ = (Index("idx_timezone_country", "country_id"),)

    def __repr__(self) -> str:
        return f"<Timezone(id={self.id}, name={self.timezone_name})>"
