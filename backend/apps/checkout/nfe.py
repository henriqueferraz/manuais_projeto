"""Provedores de NF-e (mock / Focus NFe) — T-P.4 / ADR-0009."""

from __future__ import annotations

import base64
import json
import uuid
from typing import Any
from urllib import error, request

import structlog
from django.conf import settings

from apps.orders.models import Invoice, Order

logger = structlog.get_logger(__name__)


def emit_nfe(order: Order, invoice: Invoice) -> dict[str, Any]:
    """Roteia emissão conforme NFE_PROVIDER (CI permanece em mock)."""
    provider = (getattr(settings, "NFE_PROVIDER", "mock") or "mock").lower()
    if provider == "mock":
        return _emit_mock(order, invoice)
    if provider in {"focusnfe", "focus"}:
        return _emit_focusnfe(order, invoice)
    raise RuntimeError(f"Provedor NF-e '{provider}' não suportado.")


def _emit_mock(order: Order, invoice: Invoice) -> dict[str, Any]:
    if order.notes == "force_nfe_fail":
        raise RuntimeError("Falha simulada na API fiscal.")
    key = (uuid.uuid4().hex + uuid.uuid4().hex)[:44]
    number = str(1000 + invoice.attempts)
    return {
        "access_key": key,
        "number": number,
        "series": "1",
        "pdf_url": f"https://example.local/nfe/{order.number}.pdf",
        "xml_url": f"https://example.local/nfe/{order.number}.xml",
        "provider": "mock",
    }


def _emit_focusnfe(order: Order, invoice: Invoice) -> dict[str, Any]:
    """
    Emite NF-e via Focus NFe (sandbox/homologação ou produção).
    Docs: https://focusnfe.com.br/doc/
    """
    token = getattr(settings, "FOCUSNFE_TOKEN", "") or ""
    if not token:
        raise RuntimeError("FOCUSNFE_TOKEN não configurado")

    base = (
        getattr(settings, "FOCUSNFE_BASE_URL", "") or "https://homologacao.focusnfe.com.br"
    ).rstrip("/")
    ref = f"tp-{order.number}-{invoice.attempts}".replace("/", "-")[:60]
    payload = _focus_payload(order)
    url = f"{base}/v2/nfe?ref={ref}"
    auth = base64.b64encode(f"{token}:".encode()).decode()
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=30) as resp:  # nosec B310
            raw = json.loads(resp.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        logger.warning("focusnfe_http_error", status=exc.code, detail=detail)
        raise RuntimeError(f"Focus NFe HTTP {exc.code}: {detail}") from exc

    status = str(raw.get("status") or raw.get("status_sefaz") or "")
    if status.lower() in {"erro_autorizacao", "erro", "error", "denegado"}:
        raise RuntimeError(f"Focus NFe rejeitou: {raw.get('mensagem_sefaz') or raw}")

    access_key = str(raw.get("chave_nfe") or raw.get("chave") or "")
    number = str(raw.get("numero") or invoice.attempts)
    series = str(raw.get("serie") or "1")
    return {
        "access_key": access_key or (uuid.uuid4().hex + uuid.uuid4().hex)[:44],
        "number": number,
        "series": series,
        "pdf_url": str(raw.get("caminho_danfe") or raw.get("pdf_url") or ""),
        "xml_url": str(raw.get("caminho_xml_nota_fiscal") or raw.get("xml_url") or ""),
        "provider": "focusnfe",
        "raw_status": status,
    }


def _focus_payload(order: Order) -> dict[str, Any]:
    """Payload mínimo homologável — completar CNPJ/IE do emitente via env."""
    cnpj = getattr(settings, "NFE_EMITTER_CNPJ", "") or "00000000000000"
    items = []
    for idx, item in enumerate(order.items.all(), start=1):
        items.append(
            {
                "numero_item": idx,
                "codigo_produto": item.sku,
                "descricao": (item.name or item.sku)[:120],
                "cfop": getattr(settings, "NFE_DEFAULT_CFOP", "5102"),
                "unidade_comercial": "UN",
                "quantidade_comercial": float(item.quantity),
                "valor_unitario_comercial": float(item.unit_price),
                "valor_bruto": float(item.line_total),
                "icms_situacao_tributaria": "102",
                "icms_origem": "0",
            }
        )
    return {
        "natureza_operacao": "Venda de mercadoria",
        "data_emissao": order.paid_at.isoformat() if order.paid_at else None,
        "tipo_documento": "1",
        "finalidade_emissao": "1",
        "cnpj_emitente": cnpj,
        "nome_destinatario": order.shipping_name or order.email,
        "email_destinatario": order.email,
        "logradouro_destinatario": order.shipping_street,
        "numero_destinatario": order.shipping_number or "S/N",
        "bairro_destinatario": order.shipping_district,
        "municipio_destinatario": order.shipping_city,
        "uf_destinatario": order.shipping_state,
        "cep_destinatario": "".join(c for c in (order.shipping_cep or "") if c.isdigit()),
        "itens": items,
        "valor_frete": float(order.shipping_cost or 0),
        "valor_total": float(order.total or 0),
    }
