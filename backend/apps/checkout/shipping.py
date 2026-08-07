"""Cálculo de frete — Melhor Envio (API live) + fallback fixo."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from urllib import error, request

import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ShippingOption:
    id: str
    carrier: str
    service: str
    price: Decimal
    eta_days: int
    source: str  # melhor_envio | fixed

    def as_dict(self) -> dict:
        d = asdict(self)
        d["price"] = str(self.price)
        return d


def calculate_shipping(
    *,
    cep: str,
    subtotal: Decimal,
    weight_kg: Decimal | None = None,
) -> list[ShippingOption]:
    """
    Tenta Melhor Envio se configurado; senão (ou em falha) usa frete fixo.
    """
    cep_clean = "".join(c for c in cep if c.isdigit())
    if len(cep_clean) != 8:
        raise ValueError("CEP inválido. Use 8 dígitos.")

    options: list[ShippingOption] = []
    if getattr(settings, "MELHOR_ENVIO_ENABLED", False):
        try:
            options = _quote_melhor_envio(cep_clean, weight_kg or Decimal("1.0"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("melhor_envio_failed", error=str(exc))

    if not options:
        options = _fixed_rates(cep_clean, subtotal)

    return options


def _fixed_rates(cep: str, subtotal: Decimal) -> list[ShippingOption]:
    base = Decimal(str(getattr(settings, "SHIPPING_FIXED_PRICE", "19.90")))
    express = base + Decimal("15.00")
    free_from = Decimal(str(getattr(settings, "SHIPPING_FREE_FROM", "299.00")))
    econ_price = Decimal("0.00") if subtotal >= free_from else base
    return [
        ShippingOption(
            id="fixed-econ",
            carrier="Correios",
            service="PAC (fixo)",
            price=econ_price,
            eta_days=8,
            source="fixed",
        ),
        ShippingOption(
            id="fixed-exp",
            carrier="Correios",
            service="SEDEX (fixo)",
            price=express,
            eta_days=3,
            source="fixed",
        ),
    ]


def _quote_melhor_envio(cep: str, weight_kg: Decimal) -> list[ShippingOption]:
    """
    Cotação Melhor Envio (sandbox ou produção) — T-P.4 / ADR-0010.
    https://docs.melhorenvio.com.br/
    """
    token = getattr(settings, "MELHOR_ENVIO_TOKEN", "")
    if not token:
        raise RuntimeError("MELHOR_ENVIO_TOKEN não configurado")

    # Modo stub explícito (sem rede) — útil em smoke local sem credencial válida
    if getattr(settings, "MELHOR_ENVIO_STUB", False):
        logger.info("melhor_envio_quote_stub", cep=cep, weight=str(weight_kg))
        return [
            ShippingOption(
                id="me-pac",
                carrier="Correios",
                service="PAC",
                price=Decimal("22.50"),
                eta_days=7,
                source="melhor_envio",
            ),
            ShippingOption(
                id="me-sedex",
                carrier="Correios",
                service="SEDEX",
                price=Decimal("38.90"),
                eta_days=2,
                source="melhor_envio",
            ),
        ]

    from_cep = "".join(
        c for c in str(getattr(settings, "MELHOR_ENVIO_FROM_CEP", "01310100") or "") if c.isdigit()
    )
    base = (
        getattr(settings, "MELHOR_ENVIO_BASE_URL", "") or "https://sandbox.melhorenvio.com.br"
    ).rstrip("/")
    url = f"{base}/api/v2/me/shipment/calculate"
    payload = {
        "from": {"postal_code": from_cep},
        "to": {"postal_code": cep},
        "products": [
            {
                "id": "1",
                "width": 11,
                "height": 17,
                "length": 11,
                "weight": float(weight_kg),
                "insurance_value": 0,
                "quantity": 1,
            }
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "TechPartsAI (contato@techparts.local)",
        },
    )
    try:
        with request.urlopen(req, timeout=20) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8") or "[]")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Melhor Envio HTTP {exc.code}: {detail}") from exc

    if not isinstance(data, list):
        raise RuntimeError("Resposta Melhor Envio inesperada")

    options: list[ShippingOption] = []
    for row in data:
        if row.get("error"):
            continue
        price = Decimal(str(row.get("custom_price") or row.get("price") or "0"))
        eta = int(row.get("delivery_time") or row.get("custom_delivery_time") or 5)
        company = row.get("company") or {}
        options.append(
            ShippingOption(
                id=f"me-{row.get('id')}",
                carrier=str(company.get("name") or "Melhor Envio"),
                service=str(row.get("name") or "Serviço"),
                price=price,
                eta_days=eta,
                source="melhor_envio",
            )
        )
    if not options:
        raise RuntimeError("Melhor Envio não retornou cotação válida")
    logger.info("melhor_envio_quote_live", cep=cep, count=len(options))
    return options


def pick_option(options: list[ShippingOption], option_id: str) -> ShippingOption:
    for opt in options:
        if opt.id == option_id:
            return opt
    raise ValueError("Opção de frete inválida.")
