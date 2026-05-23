from collections import defaultdict


class EventDispatcher:

    handlers = defaultdict(list)

    @classmethod
    def register(
        cls,
        event_type,
        handler,
    ):

        cls.handlers[event_type].append(
            handler
        )

    @classmethod
    async def dispatch(
        cls,
        event,
    ):

        handlers = cls.handlers.get(
            type(event),
            []
        )

        for handler in handlers:
            await handler(event)
