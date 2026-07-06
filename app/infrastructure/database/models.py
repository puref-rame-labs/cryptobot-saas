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

    invoices: Mapped[list["Invoice"]] = relationship(
        back_populates="product"
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
