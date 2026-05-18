from app.config.settings import settings


def is_admin(user_id: int) -> bool:

    return user_id in settings.ADMIN_IDS
