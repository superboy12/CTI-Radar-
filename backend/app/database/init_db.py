"""
Database initialization - creates tables and first admin user.
"""
from app.core.logging import get_logger
from app.core.security import hash_password
from app.config import settings
from app.database.session import engine, AsyncSessionLocal
from app.models import Base, User

logger = get_logger(__name__)


async def init_db() -> None:
    """Initialize the database: create all tables and seed admin user."""
    logger.info("initializing_database")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("tables_created")

    # Create first admin user if not exists
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        result = await session.execute(select(User).limit(1))
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            admin = User(
                username=settings.FIRST_ADMIN_USERNAME,
                email=settings.FIRST_ADMIN_EMAIL,
                password_hash=hash_password(settings.FIRST_ADMIN_PASSWORD),
                role="ADMIN",
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            logger.info("admin_user_created", username=settings.FIRST_ADMIN_USERNAME)
        else:
            logger.info("admin_user_exists", username=existing_user.username)

    logger.info("database_initialized")
