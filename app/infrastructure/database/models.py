from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    ForeignKey,
    BigInteger,
    String,
    DateTime,
    Boolean,
    Numeric,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.infrastructure.database.base import Base
from app.domain.invoice.state_machine import InvoiceState as InvoiceStatus


# -------------------------
# PRODUCT STATUS (DOMAIN EXTENSION)
# -------------------------
class ProductStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    PUBLISHED = "PUBLISHED"


# -------------------------
# USER
# -------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
    )

    username: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="user"
    )


# -------------------------
# PRODUCT
# -------------------------
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="USDT",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    telegram_file_id: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    file_type: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    # VECTOR 1 — PRODUCT READINESS STATE
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ProductStatus.DRAFT.value,
    )

    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id"),
        nullable=False,
    )

    brand: Mapped["Brand"] = relationship(
        back_populates="products"
    )

    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="product"
    )


# -------------------------
# CATEGORY
# -------------------------
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    subcategories: Mapped[list["Subcategory"]] = relationship(
        back_populates="category"
    )


# -------------------------
# SUBCATEGORY
# -------------------------
class Subcategory(Base):
    __tablename__ = "subcategories"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
    )

    category: Mapped["Category"] = relationship(
        back_populates="subcategories"
    )

    product_groups: Mapped[list["ProductGroup"]] = relationship(
        back_populates="subcategory"
    )


# -------------------------
# PRODUCT GROUP
# -------------------------
class ProductGroup(Base):
    __tablename__ = "product_groups"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    subcategory_id: Mapped[int] = mapped_column(
        ForeignKey("subcategories.id"),
        nullable=False,
    )

    subcategory: Mapped["Subcategory"] = relationship(
        back_populates="product_groups"
    )

    brands: Mapped[list["Brand"]] = relationship(
        back_populates="product_group"
    )


# -------------------------
# BRAND
# -------------------------
class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    product_group_id: Mapped[int] = mapped_column(
        ForeignKey("product_groups.id"),
        nullable=False,
    )

    product_group: Mapped["ProductGroup"] = relationship(
        back_populates="brands"
    )

    products: Mapped[list["Product"]] = relationship(
        back_populates="brand"
    )


# -------------------------
# INVOICE
# -------------------------
class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=InvoiceStatus.PENDING.value
        if hasattr(InvoiceStatus.PENDING, "value")
        else InvoiceStatus.PENDING,
    )

    tx_hash: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )

    provider: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    external_payment_id: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )


    user: Mapped["User"] = relationship(
        back_populates="invoices"
    )

    product: Mapped["Product"] = relationship(
        back_populates="invoices"
    )


# -------------------------
# PAYMENT EVENT
# -------------------------
class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
    )

    payload: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    retry_count: Mapped[int] = mapped_column(
        default=0,
    )

    failed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    last_error: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    invoice: Mapped["Invoice"] = relationship()
