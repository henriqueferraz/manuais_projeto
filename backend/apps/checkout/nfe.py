"""Provedores de NF-e (mock / Focus NFe / NotaAS) — T-P.4 / ADR-0009."""

from __future__ import annotations

import base64
import json
import time
import uuid
from typing import Any
from urllib import error, request

import structlog
from django.conf import settings

from apps.orders.models import Invoice, Order

logger = structlog.get_logger(__name__)

# IBGE mínimo para destinos comuns (fallback: NFE_DEFAULT_IBGE_CODE).
_IBGE_BY_CITY_UF: dict[tuple[str, str], int] = {
    ("sao paulo", "SP"): 3550308,
    ("são paulo", "SP"): 3550308,
    ("sp", "SP"): 3550308,
    ("rio de janeiro", "RJ"): 3304557,
    ("belo horizonte", "MG"): 3106200,
    ("curitiba", "PR"): 4106902,
    ("porto alegre", "RS"): 4314902,
    ("brasilia", "DF"): 5300108,
    ("brasília", "DF"): 5300108,
    ("salvador", "BA"): 2927408,
    ("fortaleza", "CE"): 2304400,
    ("recife", "PE"): 2611606,
    ("manaus", "AM"): 1302603,
    ("belem", "PA"): 1501402,
    ("belém", "PA"): 1501402,
    ("goiania", "GO"): 5208707,
    ("goiânia", "GO"): 5208707,
}


def emit_nfe(order: Order, invoice: Invoice) -> dict[str, Any]:
    """Roteia emissão conforme NFE_PROVIDER (CI permanece em mock)."""
    provider = (getattr(settings, "NFE_PROVIDER", "mock") or "mock").lower()
    if provider == "mock":
        return _emit_mock(order, invoice)
    if provider in {"focusnfe", "focus"}:
        return _emit_focusnfe(order, invoice)
    if provider in {"notaas", "notaas.com", "notaas.com.br"}:
        return _emit_notaas(order, invoice)
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


def _emit_notaas(order: Order, invoice: Invoice) -> dict[str, Any]:
    """
    Emite NF-e via NotaAS (assíncrono + polling).
    Docs: https://docs.notaas.com.br/docs/nfe/endpoints
    """
    api_key = getattr(settings, "API_KEY_NOTAAS", "") or ""
    if not api_key:
        raise RuntimeError("API_KEY_NOTAAS não configurado")

    base = (
        getattr(settings, "NOTAAS_BASE_URL", "") or "https://platform.notaas.com.br/api/v1"
    ).rstrip("/")
    payload = _notaas_payload(order)
    url = f"{base}/nfe/emitir"
    raw = _notaas_request("POST", url, api_key, payload)

    invoice_id = str(raw.get("invoiceId") or raw.get("id") or "")
    if not invoice_id:
        raise RuntimeError(f"NotaAS sem invoiceId: {raw}")

    status_payload = _notaas_poll_status(base, api_key, invoice_id)
    status = str(status_payload.get("status") or "").lower()
    if status == "error":
        raise RuntimeError(f"NotaAS rejeitou: {status_payload.get('xMotivo') or status_payload}")
    if status != "issued":
        raise RuntimeError(f"NotaAS status inesperado após polling: {status_payload}")

    access_key = str(status_payload.get("chaveAcesso") or "")
    number = str(
        status_payload.get("nNF")
        or status_payload.get("numero")
        or status_payload.get("nNFSe")
        or invoice.attempts
    )
    series = str(status_payload.get("serie") or status_payload.get("series") or "1")
    pdf_url = str(status_payload.get("pdfUrl") or f"{base}/nfe/invoices/{invoice_id}/danfe")
    xml_url = str(status_payload.get("xmlUrl") or f"{base}/nfe/invoices/{invoice_id}/xml")
    return {
        "access_key": access_key or (uuid.uuid4().hex + uuid.uuid4().hex)[:44],
        "number": number,
        "series": series,
        "pdf_url": pdf_url,
        "xml_url": xml_url,
        "provider": "notaas",
        "invoice_id": invoice_id,
        "raw_status": status,
    }


def _notaas_poll_status(base: str, api_key: str, invoice_id: str) -> dict[str, Any]:
    url = f"{base}/nfe/invoices/{invoice_id}/status"
    # Emissão SEFAZ pode levar alguns segundos; Celery já retenta a task.
    deadline = time.monotonic() + 45
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        last = _notaas_request("GET", url, api_key)
        status = str(last.get("status") or "").lower()
        if status in {"issued", "error", "cancelled", "inutilized"}:
            return last
        time.sleep(2)
    return last


def _notaas_request(
    method: str, url: str, api_key: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json",
        # Sem UA o edge Cloudflare pode responder 1010/403.
        "User-Agent": "TechPartsAI/1.0 (+nfe-notaas)",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=45) as resp:  # nosec B310
            body = resp.read().decode("utf-8") or "{}"
            return json.loads(body) if body.strip() else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        logger.warning("notaas_http_error", status=exc.code, detail=detail, url=url)
        raise RuntimeError(f"NotaAS HTTP {exc.code}: {detail}") from exc


def _notaas_payload(order: Order) -> dict[str, Any]:
    document = _digits(
        getattr(order, "customer_document", "")
        or getattr(settings, "NFE_DEFAULT_DEST_DOCUMENT", "")
        or ""
    )
    if len(document) not in {11, 14}:
        raise RuntimeError(
            "Destinatário sem CPF/CNPJ: informe NFE_DEFAULT_DEST_DOCUMENT "
            "ou customer_document no pedido."
        )

    dest: dict[str, Any] = {
        "nome": (order.shipping_name or order.email or "Cliente")[:120],
        "email": order.email,
        "indicadorIE": 9,
        "endereco": {
            "logradouro": order.shipping_street or "Não informado",
            "numero": order.shipping_number or "SN",
            "complemento": order.shipping_complement or "",
            "bairro": order.shipping_district or "Centro",
            "codigoMunicipio": _ibge_code(order.shipping_city, order.shipping_state),
            "cidade": order.shipping_city or "São Paulo",
            "uf": (order.shipping_state or "SP")[:2].upper(),
            "cep": _digits(order.shipping_cep),
        },
    }
    if len(document) == 11:
        dest["cpf"] = document
    else:
        dest["cnpj"] = document

    cfop = str(getattr(settings, "NFE_DEFAULT_CFOP", "5102") or "5102")
    ncm = str(getattr(settings, "NFE_DEFAULT_NCM", "85437099") or "85437099")
    csosn = str(getattr(settings, "NFE_DEFAULT_CSOSN", "102") or "102")
    items: list[dict[str, Any]] = []
    for item in order.items.all():
        qty = float(item.quantity)
        unit = float(item.unit_price)
        total = float(item.line_total)
        product_ncm = ncm
        specs = getattr(getattr(item, "product", None), "specs", None) or {}
        if isinstance(specs, dict) and specs.get("ncm"):
            product_ncm = _digits(str(specs["ncm"]))[:8] or ncm
        items.append(
            {
                "descricao": (item.name or item.sku)[:120],
                "codigo": item.sku,
                "ncm": product_ncm,
                "cfop": cfop,
                "quantidade": qty,
                "valorUnitario": unit,
                "valorTotal": total,
                "unidade": "UN",
                "csosn": csosn,
            }
        )
    if not items:
        raise RuntimeError("Pedido sem itens para NF-e NotaAS.")

    total = float(order.total or 0)
    freight = float(order.shipping_cost or 0)
    return {
        "modelo": 55,
        "naturezaOperacao": "Venda de mercadoria",
        "tipoOperacao": 1,
        "finalidade": 1,
        "consumidorFinal": 1,
        "presencaComprador": 2,
        "indicadorIntermediador": 0,
        "dest": dest,
        "items": items,
        "valorFrete": freight,
        "transporte": {"modalidadeFrete": 0 if freight > 0 else 9},
        "pagamentos": [{"tipoPagamento": "03", "valor": total}],
        "infCpl": f"Pedido {order.number}",
    }


def _digits(value: str) -> str:
    return "".join(c for c in (value or "") if c.isdigit())


def _ibge_code(city: str, uf: str) -> int:
    key = ((city or "").strip().lower(), (uf or "").strip().upper())
    if key in _IBGE_BY_CITY_UF:
        return _IBGE_BY_CITY_UF[key]
    default = getattr(settings, "NFE_DEFAULT_IBGE_CODE", "3550308") or "3550308"
    try:
        return int(_digits(str(default)) or "3550308")
    except ValueError:
        return 3550308


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
