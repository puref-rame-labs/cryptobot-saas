import hashlib
import hmac
import json
import logging
from decimal import Decimal

import httpx

from app.application.payments.providers.base import BasePaymentProvider
from app.domain.payment.dto.payment_event_dto import PaymentEventDTO
from app.config.settings import settings


logger = logging.getLogger(__name__)


BTCPAY_EVENT_STATUS_MAP = {
    "InvoiceSettled": "paid",
    "InvoiceExpired": "expired",
    "InvoiceInvalid": "failed",
    "InvoiceProcessing": "processing",
}


class BTCPayProvider(BasePaymentProvider):

    def __init__(self, network: str = "mainnet"):
        self._network = network

        if network == "mainnet":
            host = settings.BTCPAY_MAINNET_HOST
            self._public_host = settings.BTCPAY_MAINNET_PUBLIC_HOST or host
            self._api_key = settings.BTCPAY_MAINNET_API_KEY
            self._store_id = settings.BTCPAY_MAINNET_STORE_ID
            self._webhook_secret = settings.BTCPAY_MAINNET_WEBHOOK_SECRET
        elif network == "testnet":
            host = settings.BTCPAY_TESTNET_HOST
            self._public_host = settings.BTCPAY_TESTNET_PUBLIC_HOST or host
            self._api_key = settings.BTCPAY_TESTNET_API_KEY
            self._store_id = settings.BTCPAY_TESTNET_STORE_ID
            self._webhook_secret = settings.BTCPAY_TESTNET_WEBHOOK_SECRET
        else:
            raise ValueError(f"Unknown network: {network}")

        self.API_URL = f"{host.rstrip('/')}/api/v1/stores/{self._store_id}"

    async def create_invoice(self, invoice) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.API_URL}/invoices",
                headers={
                    "Authorization": f"token {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "amount": str(invoice.amount),
                    "currency": invoice.currency,
                    "metadata": {"orderId": str(invoice.id)},
                },
            )
            if response.status_code >= 400:
                logger.error(
                    "BTCPay create_invoice failed: %s %s",
                    response.status_code, response.text,
                )
            response.raise_for_status()
            data = response.json()

        return type("BTCPayInvoiceResponse", (), {
            "external_id": data["id"],
            "payment_url": f"{self._public_host.rstrip('/')}/i/{data['id']}",
        })()

    async def verify_signature(
        self,
        headers: dict,
        payload: dict | str,
    ) -> bool:
        signature_header = headers.get("btcpay-sig", "")

        if isinstance(payload, dict):
            body = json.dumps(payload, separators=(",", ":"))
        else:
            body = payload

        expected = "sha256=" + hmac.new(
            self._webhook_secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature_header, expected)

    async def normalize(self, payload: dict) -> PaymentEventDTO:
        event_type = payload.get("type", "unknown")
        status = BTCPAY_EVENT_STATUS_MAP.get(event_type, event_type)
        invoice_id = str(payload["invoiceId"])

        paid_asset = None
        paid_amount = None
        paid_fiat_rate = None

        if status == "paid":
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_URL}/invoices/{invoice_id}/payment-methods",
                    headers={"Authorization": f"token {self._api_key}"},
                )
                response.raise_for_status()
                methods = response.json()

            # Non-custodial BTC-only provider (see btcpay_provider.md):
            # asset is effectively constant. Only BTC-CHAIN is enabled
            # in the Store checkout config today (no Lightning yet).
            btc_method = next(
                (m for m in methods if m.get("paymentMethodId") == "BTC-CHAIN"),
                None,
            )
            if btc_method:
                paid_asset = "BTC"
                paid_amount = Decimal(btc_method["totalPaid"])
                # NOTE: rate here is fixed at invoice creation time,
                # not at payment time (unlike CryptoBot) - see
                # "Rate-Lock Semantics" in btcpay_provider.md.
                paid_fiat_rate = Decimal(btc_method["rate"])

        return PaymentEventDTO(
            external_payment_id=invoice_id,
            status=status,
            tx_hash=None,
            paid_asset=paid_asset,
            paid_amount=paid_amount,
            paid_fiat_rate=paid_fiat_rate,
        )
