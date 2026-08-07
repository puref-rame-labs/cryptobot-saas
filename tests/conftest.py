from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest_asyncio
from sqlalchemy import text

import app.infrastructure.database.session as session_module
from app.infrastructure.database.models import (
    User, Product, Category, Subcategory, ProductGroup, Brand, Invoice,
)
import app.application.bot_instance as bot_instance


TABLES_TRUNCATE_ORDER = [
    "payment_events",
    "invoices",
    "products",
    "brands",
    "product_groups",
    "subcategories",
    "categories",
    "users",
]


async def _reset_engine():
    if session_module._engine is not None:
        try:
            await session_module._engine.dispose()
        except Exception:
            pass
    session_module._engine = None
    session_module._async_session = None


@pytest_asyncio.fixture(autouse=True)
async def reset_engine_per_test():
    """
    get_engine()/get_sessionmaker() - модульные синглтоны, но pytest-asyncio
    создаёт новый event loop под каждый тест (function scope). asyncpg-
    соединение, созданное в loop одного теста, нельзя использовать в loop
    следующего - отсюда 'attached to a different loop'. Сбрасываем синглтон
    в начале и в конце каждого теста, чтобы engine всегда создавался заново
    внутри текущего активного loop.
    """
    await _reset_engine()
    yield
    await _reset_engine()


@pytest_asyncio.fixture
async def db_session(reset_engine_per_test):
    sessionmaker = session_module.get_sessionmaker()
    session = sessionmaker()
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(reset_engine_per_test):
    sessionmaker = session_module.get_sessionmaker()
    session = sessionmaker()
    try:
        for table in TABLES_TRUNCATE_ORDER:
            await session.execute(
                text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
            )
        await session.commit()
    finally:
        await session.close()
    yield


@pytest_asyncio.fixture
async def seeded_invoice(db_session, clean_db):
    category = Category(title="Электроника")
    db_session.add(category)
    await db_session.flush()

    subcategory = Subcategory(title="Планшеты", category_id=category.id)
    db_session.add(subcategory)
    await db_session.flush()

    product_group = ProductGroup(title="iPad", subcategory_id=subcategory.id)
    db_session.add(product_group)
    await db_session.flush()

    brand = Brand(title="Apple", product_group_id=product_group.id)
    db_session.add(brand)
    await db_session.flush()

    user = User(telegram_id=111222333, username="tester")
    db_session.add(user)
    await db_session.flush()

    product = Product(
        title="Test Product",
        price=Decimal("1000.00"),
        currency="RUB",
        status="PUBLISHED",
        brand_id=brand.id,
        telegram_file_id="FAKE_FILE_ID",
        file_type="document",
    )
    db_session.add(product)
    await db_session.flush()

    invoice = Invoice(
        user_id=user.id,
        product_id=product.id,
        amount=Decimal("1000.00"),
        currency="RUB",
        status="PENDING",
        provider="cryptobot",
        external_payment_id="ext-race-001",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db_session.add(invoice)
    await db_session.commit()

    return invoice.id


@pytest_asyncio.fixture
async def seeded_invoice_no_file(db_session, clean_db):
    category = Category(title="Электроника")
    db_session.add(category)
    await db_session.flush()

    subcategory = Subcategory(title="Планшеты", category_id=category.id)
    db_session.add(subcategory)
    await db_session.flush()

    product_group = ProductGroup(title="iPad", subcategory_id=subcategory.id)
    db_session.add(product_group)
    await db_session.flush()

    brand = Brand(title="Apple", product_group_id=product_group.id)
    db_session.add(brand)
    await db_session.flush()

    user = User(telegram_id=444555666, username="tester_no_file")
    db_session.add(user)
    await db_session.flush()

    product = Product(
        title="Product Without File",
        price=Decimal("500.00"),
        currency="RUB",
        status="PUBLISHED",
        brand_id=brand.id,
        telegram_file_id=None,
        file_type=None,
    )
    db_session.add(product)
    await db_session.flush()

    invoice = Invoice(
        user_id=user.id,
        product_id=product.id,
        amount=Decimal("500.00"),
        currency="RUB",
        status="PENDING",
        provider="cryptobot",
        external_payment_id="ext-nofile-001",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db_session.add(invoice)
    await db_session.commit()

    return invoice.id


@pytest_asyncio.fixture(autouse=True)
def mock_bot():
    fake_bot = AsyncMock()
    bot_instance.bot = fake_bot
    yield fake_bot
    bot_instance.bot = None
