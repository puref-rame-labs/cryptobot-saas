import hashlib
import hmac
import json
from decimal import Decimal

import httpx

from app.application.payments.providers.base import BasePaymentProvider
from app.domain.payment.dto.payment_event_dto import PaymentEventDTO
from app.config.settings import settings


class CryptoBotProvider(BasePaymentProvider):

    API_URL = "https://testnet-pay.crypt.bot/api"

    def __init__(self):
        self._token = settings.CRYPTOBOT_TOKEN

    async def create_invoice(self, invoice) -> dict:
        async with httpx.AsyncClient(proxy="socks5://127.0.0.1:10808") as client:
            response = await client.post(
                f"{self.API_URL}/createInvoice",
                headers={"Crypto-Pay-API-Token": self._token},
                json={
                    "currency_type": "fiat",
                    "fiat": invoice.currency,
                    "amount": str(invoice.amount),
                    "description": f"Invoice #{invoice.id}",
                    "expires_in": 900,
                },
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("ok"):
            raise ValueError(f"CryptoBot error: {data}")

        result = data["result"]

        return type("CryptoBotInvoiceResponse", (), {
            "external_id": str(result["invoice_id"]),
            "payment_url": result["pay_url"],
        })()

    async def verify_signature(
        self,
        headers: dict,
        payload: dict | str,
    ) -> bool:
        signature = headers.get("crypto-pay-api-signature", "")

        if isinstance(payload, dict):
            body = json.dumps(payload, separators=(",", ":"))
        else:
            body = payload

        secret = hashlib.sha256(self._token.encode()).digest()
        expected = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()

        return hmac.compare_digest(signature, expected)

    async def normalize(self, payload: dict) -> PaymentEventDTO:
        invoice = payload.get("payload", payload)

        paid_asset = invoice.get("paid_asset")
        paid_amount = invoice.get("paid_amount")
        paid_fiat_rate = invoice.get("paid_fiat_rate")

        return PaymentEventDTO(
            external_payment_id=str(invoice["invoice_id"]),
            status="paid" if payload.get("update_type") == "invoice_paid" else invoice.get("status", "unknown"),
            tx_hash=None,
            paid_asset=paid_asset,
            paid_amount=Decimal(str(paid_amount)) if paid_amount else None,
            paid_fiat_rate=Decimal(str(paid_fiat_rate)) if paid_fiat_rate else None,
        )
