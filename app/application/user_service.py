import secrets


class UserService:
    def __init__(self, uow):
        self.uow = uow

    async def _generate_unique_referral_code(self) -> str:

        while True:
            candidate = secrets.token_urlsafe(6)

            existing = await self.uow.users.get_by_referral_code(candidate)

            if not existing:
                return candidate

    async def register_user(
        self,
        telegram_id: int,
        username: str | None,
        ref_code: str | None = None,
    ):

        existing = await self.uow.users.get_by_telegram_id(telegram_id)

        if existing:
            # referred_by_id is immutable once set (referral_program.md) -
            # returning users are NEVER re-processed for referral linking,
            # regardless of what ref_code they arrive with this time.
            return existing

        referred_by_id = None

        if ref_code:
            referrer = await self.uow.users.get_by_referral_code(ref_code)

            if referrer:
                referred_by_id = referrer.id

        referral_code = await self._generate_unique_referral_code()

        user = await self.uow.users.create_user(
            telegram_id=telegram_id,
            username=username,
            referral_code=referral_code,
            referred_by_id=referred_by_id,
        )

        # Defensive guard against self-referral (referral_program.md:
        # "A user CANNOT refer themselves"). Not reachable in practice
        # since a brand-new user cannot yet own the referral_code they
        # were invited with, but kept as an explicit invariant check.
        if user.referred_by_id == user.id:
            user.referred_by_id = None

        return user
