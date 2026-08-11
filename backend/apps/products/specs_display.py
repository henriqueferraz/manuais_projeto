"""Exibição de especificações técnicas em português (catálogo)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

# Chave canônica (snake_case) → rótulo pt-BR para o usuário
SPEC_LABELS_PT: dict[str, str] = {
    "blade_count": "Nº de pás",
    "diameter_cm": "Diâmetro (cm)",
    "material": "Material",
    "color": "Cor",
    "rpm": "RPM",
    "mounting": "Fixação / montagem",
    "bearing_type": "Tipo de rolamento",
    "remote_included": "Controle remoto incluso",
    "ncm": "NCM",
    "ncm_classification": "Classificação NCM",
    "power_w": "Potência (W)",
    "weight_kg": "Peso (kg)",
    "voltage": "Voltagem",
    "height_cm": "Altura (cm)",
    "width_cm": "Largura (cm)",
    "depth_cm": "Profundidade (cm)",
    "height": "Altura",
    "width": "Largura",
    "depth": "Profundidade",
    "altura_cm": "Altura (cm)",
    "largura_cm": "Largura (cm)",
    "profundidade_cm": "Profundidade (cm)",
    "capacity": "Capacidade",
    "ean": "EAN",
    "barcode": "Código de barras",
    "frequency_hz": "Frequência (Hz)",
    "consumption_kwh": "Consumo (kWh)",
    "packaging_qty": "Quantidade por embalagem",
    "model_variants": "Variantes de modelo",
    "safety_warnings": "Avisos de segurança",
    "key_usage_steps": "Como utilizar",
    "installation_requirements": "Requisitos de instalação",
    "certifications": "Certificações",
    "notes": "Observações",
    "warranty": "Garantia",
    "warranty_legal_days": "Garantia legal (dias)",
    "warranty_additional_days": "Garantia adicional (dias)",
    "warranty_total_days": "Garantia total (dias)",
    "legal_days": "Garantia legal (dias)",
    "additional_days": "Garantia adicional (dias)",
    "total_days": "Garantia total (dias)",
    "jar_material": "Material do copo",
    "speeds": "Velocidades",
    "part_code": "Código da peça",
    "ref_number": "Referência no diagrama",
    "qty_per_unit": "Qtd. por unidade",
}

# Aliases / chaves com ponto → canônico
SPEC_KEY_ALIASES: dict[str, str] = {
    "warranty.legal_days": "warranty_legal_days",
    "warranty.additional_days": "warranty_additional_days",
    "warranty.total_days": "warranty_total_days",
    "warranty_legal_days": "warranty_legal_days",
    "warranty_additional_days": "warranty_additional_days",
    "warranty_total_days": "warranty_total_days",
    "potencia": "power_w",
    "potência": "power_w",
    "power": "power_w",
    "potencia_w": "power_w",
    "potência_w": "power_w",
}

# Não exibir na PDP (metadado interno / ruído)
HIDDEN_SPEC_KEYS: set[str] = {
    "source_doc_types",
    "low_confidence_fields",
    "document_conflicts",
    "manufacturer",
    "parent_sku",
    "parent_model_code",
    "assembly_summary",
    "troubleshooting",
}


def canonicalize_spec_key(key: str) -> str:
    """Normaliza chave técnica: minúsculas, ponto/espaço/hífen → underscore."""
    raw = (key or "").strip()
    if not raw:
        return ""
    lower = raw.replace("-", "_").replace(".", "_").replace(" ", "_").lower()
    lower = "_".join(p for p in lower.split("_") if p)
    return SPEC_KEY_ALIASES.get(lower, SPEC_KEY_ALIASES.get(raw.lower(), lower))


def label_for_spec_key(key: str) -> str:
    """Retorna rótulo em português; a chave técnica permanece no armazenamento."""
    normalized = canonicalize_spec_key(key)
    if not normalized:
        return ""
    if normalized in SPEC_LABELS_PT:
        return SPEC_LABELS_PT[normalized]
    # fallback: humaniza em português simples (sem Title Case inglês agressivo)
    words = normalized.split("_")
    text = " ".join(words).strip()
    if not text:
        return ""
    return text[:1].upper() + text[1:]


def format_spec_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, Decimal):
        normalized = value.normalize()
        text = format(normalized, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text.replace(".", ",")
    if isinstance(value, float):
        text = f"{value:.10g}"
        return text.replace(".", ",")
    if isinstance(value, (list, tuple)):
        return "; ".join(format_spec_value(item) for item in value if item not in (None, ""))
    if isinstance(value, dict):
        # dict genérico: só pares com rótulo PT (não dump cru)
        parts: list[str] = []
        for k, v in value.items():
            if v in (None, "", [], {}):
                continue
            parts.append(f"{label_for_spec_key(str(k))}: {format_spec_value(v)}")
        return "; ".join(parts)
    text = str(value).strip()
    lowered = text.lower()
    if lowered in {"true", "yes", "sim"}:
        return "Sim"
    if lowered in {"false", "no", "nao", "não"}:
        return "Não"
    # Listas serializadas com "; " no specs_extra
    if "; " in text and len(text) > 80:
        return text
    return text


def _expand_warranty(value: Any) -> list[tuple[str, Any]]:
    """Converte objeto/dict de garantia em pares canônicos."""
    if value in (None, "", {}, []):
        return []
    data: dict[str, Any]
    if isinstance(value, dict):
        data = {canonicalize_spec_key(str(k)): v for k, v in value.items()}
    else:
        return []
    mapping = {
        "legal_days": "warranty_legal_days",
        "additional_days": "warranty_additional_days",
        "total_days": "warranty_total_days",
        "warranty_legal_days": "warranty_legal_days",
        "warranty_additional_days": "warranty_additional_days",
        "warranty_total_days": "warranty_total_days",
    }
    out: list[tuple[str, Any]] = []
    for raw_key, canon in mapping.items():
        if raw_key in data and data[raw_key] not in (None, ""):
            # evita duplicar se já veio canônico
            if any(k == canon for k, _ in out):
                continue
            out.append((canon, data[raw_key]))
    return out


def product_spec_rows(product) -> list[tuple[str, str]]:
    """
    Linhas (rótulo pt-BR, valor) para a PDP.

    Mantém as chaves técnicas no JSON do produto; só o rótulo exibido é traduzido.
    Deduplica garantia (objeto vs warranty.* flat).
    """
    rows: list[tuple[str, str]] = []
    seen_labels: set[str] = set()
    seen_keys: set[str] = set()

    def add(key: str, value: Any) -> None:
        canon = canonicalize_spec_key(key)
        if not canon or canon in HIDDEN_SPEC_KEYS:
            return
        if value in (None, "", {}, []):
            return
        if canon in seen_keys:
            return
        label = label_for_spec_key(canon)
        if not label or label in seen_labels:
            return
        formatted = format_spec_value(value)
        if not formatted:
            return
        seen_keys.add(canon)
        seen_labels.add(label)
        rows.append((label, formatted))

    add("voltage", getattr(product, "voltage", None))
    add("power_w", getattr(product, "power_w", None))
    add("weight_kg", getattr(product, "weight_kg", None))

    dimensions = getattr(product, "dimensions", None) or {}
    if isinstance(dimensions, dict):
        for key, value in dimensions.items():
            add(str(key), value)

    specs = getattr(product, "specs", None) or {}
    if not isinstance(specs, dict):
        return rows

    # 1) Garantia: expandir objeto e ignorar depois as chaves flat duplicadas
    warranty_keys_from_object: set[str] = set()
    if "warranty" in specs:
        for canon, value in _expand_warranty(specs.get("warranty")):
            add(canon, value)
            warranty_keys_from_object.add(canon)

    # 2) Demais specs (pula warranty bruto e flats já cobertos pelo objeto)
    for key, value in specs.items():
        canon = canonicalize_spec_key(str(key))
        if canon == "warranty":
            continue
        if canon in warranty_keys_from_object:
            continue
        # flats de garantia mesmo sem objeto
        if canon in {
            "warranty_legal_days",
            "warranty_additional_days",
            "warranty_total_days",
            "legal_days",
            "additional_days",
            "total_days",
        } and warranty_keys_from_object:
            continue
        add(str(key), value)

    return rows
