class DeliveryError(Exception):
    """Base exception for delivery errors."""


class ProductFileMissing(DeliveryError):
    """Raised when product has no attached Telegram file."""
