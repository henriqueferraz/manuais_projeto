"""Cálculo de frete — Melhor Envio (stub) + fallback fixo."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal

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
    # Frete grátis simbólico acima do limiar
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
    Integração Melhor Envio — requer token.
    Em ausência de token real, levanta para acionar fallback.
    """
    token = getattr(settings, "MELHOR_ENVIO_TOKEN", "")
    if not token:
        raise RuntimeError("MELHOR_ENVIO_TOKEN não configurado")

    # Stub estruturado: em produção chamar API REST Melhor Envio
    # https://docs.melhorenvio.com.br/
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


def pick_option(options: list[ShippingOption], option_id: str) -> ShippingOption:
    for opt in options:
        if opt.id == option_id:
            return opt
    raise ValueError("Opção de frete inválida.")
