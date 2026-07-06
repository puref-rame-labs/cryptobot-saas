# app/services/payments/core/models/payment_status.py

class PaymentStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    DELIVERED = "DELIVERED"
