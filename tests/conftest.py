from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import app.infrastructure.database.session as session_module
from app.config.settings import settings
from app.infrastructure.database.models import (
    User, Product, Category, Subcategory, ProductGroup, Brand, Invoice,
)
import app.application.bot_instance as bot_instance


def _require_test_database_url() -> str:
    """
    Guard against accidentally running destructive test fixtures
    (TRUNCATE ... CASCADE in clean_db below) against the dev/runtime
    database. TEST_DATABASE_URL must be explicitly configured and must
    look like a test database - see known_issues.md, "shared test/dev
    database" entry (2026-08-15).
    """
    url = settings.TEST_DATABASE_URL
    if not url:
        raise RuntimeError(
            "TEST_DATABASE_URL is not set. Refusing to run tests against "
            "DATABASE_URL (the dev/runtime database) - see known_issues.md."
        )
    if "test" not in url.lower():
        raise RuntimeError(
            f"TEST_DATABASE_URL does not look like a test database "
            f"(no 'test' in the URL): {url!r}. Refusing to run destructive "
            f"fixtures against it."
        )
    return url


TABLES_TRUNCATE_ORDER = [
    "referral_accruals",
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

    Additionally, force get_engine()/get_sessionmaker() to point at
    TEST_DATABASE_URL for the duration of the test, instead of
    DATABASE_URL. This prevents tests from ever touching the dev/
    runtime database, even if DATABASE_URL is misconfigured to point
    at the same place TEST_DATABASE_URL does (or vice versa) - see
    _require_test_database_url() above.
    """
    test_url = _require_test_database_url()

    await _reset_engine()

    session_module._engine = create_async_engine(
        test_url,
        echo=settings.DB_ECHO,
    )
    session_module._async_session = async_sessionmaker(
        bind=session_module._engine,
        class_=session_module.AsyncSession,
        expire_on_commit=False,
    )

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
async def seeded_invoice_with_referrer(db_session, clean_db):
    """
    referral_program.md: a PAID invoice belonging to a user with
    referred_by_id set, used to test accrual creation + idempotency.
    """
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

    referrer = User(
        telegram_id=777888999,
        username="referrer_user",
        referral_code="REF123",
    )
    db_session.add(referrer)
    await db_session.flush()

    referred_user = User(
        telegram_id=111000222,
        username="referred_user",
        referred_by_id=referrer.id,
    )
    db_session.add(referred_user)
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
        user_id=referred_user.id,
        product_id=product.id,
        amount=Decimal("1000.00"),
        currency="RUB",
        status="PENDING",
        provider="cryptobot",
        external_payment_id="ext-referral-001",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db_session.add(invoice)
    await db_session.commit()

    return {
        "invoice_id": invoice.id,
        "referrer_id": referrer.id,
        "referred_user_id": referred_user.id,
    }


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
