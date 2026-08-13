"""Resolve tipo de produto / modelo a partir da sessão ou do relato do cliente."""

from __future__ import annotations

import re
from dataclasses import dataclass

from django.db.models import Q

# Aliases comuns → termo de categoria no catálogo
_TYPE_ALIASES: tuple[tuple[str, str], ...] = (
    ("liquidificador", "liquidificador"),
    ("ventilador", "ventilador"),
    ("batedeira", "batedeira"),
    ("air fryer", "air fryer"),
    ("airfryer", "air fryer"),
    ("frigideira", "frigideira"),
    ("geladeira", "geladeira"),
    ("refrigerador", "geladeira"),
    ("micro[- ]?ondas", "microondas"),
    ("lavadora", "lavadora"),
    ("máquina de lavar", "lavadora"),
    ("maquina de lavar", "lavadora"),
    ("secadora", "secadora"),
    ("aspirador", "aspirador"),
    ("ferro de passar", "ferro"),
    ("cafeteira", "cafeteira"),
    ("panela de pressão", "panela"),
    ("cooktop", "cooktop"),
    ("fogão", "fogão"),
    ("forno", "forno"),
)

# Códigos de modelo típicos: VTE-02, BLSTMG-BR8, NM-100, VT40NB
_MODEL_CODE_RE = re.compile(
    r"\b([A-Z]{1,8}(?:-?[A-Z0-9]{1,8}){0,3}\d[A-Z0-9-]{0,12})\b",
    re.I,
)


@dataclass(frozen=True)
class ProductContext:
    """Contexto de produto para restringir o RAG de diagnóstico."""

    product_id: int | None = None
    category_id: int | None = None
    category_name: str = ""
    model_code: str = ""
    product_type: str = ""
    source: str = ""  # session | text_model | text_type | none

    @property
    def has_context(self) -> bool:
        return bool(
            self.product_id
            or self.category_id
            or self.category_name
            or self.model_code
            or self.product_type
        )


def resolve_product_context(
    symptom: str,
    *,
    product_id: int | None = None,
    category_id: int | None = None,
) -> ProductContext:
    """
    Verifica se o cliente (ou a sessão) informou tipo de produto ou modelo.

    Prioridade: product_id da sessão → category_id → modelo no texto → tipo no texto.
    """
    if product_id:
        from apps.products.models import Product

        product = (
            Product.objects.filter(pk=product_id)
            .select_related("category", "equipment_model")
            .first()
        )
        if product:
            return ProductContext(
                product_id=product.pk,
                category_id=product.category_id or category_id,
                category_name=(product.category.name if product.category_id else ""),
                model_code=(
                    product.model_code or getattr(product.equipment_model, "code", "") or ""
                ),
                product_type=(product.category.name if product.category_id else ""),
                source="session",
            )

    if category_id:
        from apps.catalog.models import Category

        cat = Category.objects.filter(pk=category_id).first()
        if cat:
            return ProductContext(
                category_id=cat.pk,
                category_name=cat.name,
                product_type=cat.name,
                source="session",
            )

    text = _strip_locale_prefix(symptom or "")
    model_ctx = _resolve_model_from_text(text)
    if model_ctx.has_context:
        return model_ctx

    type_ctx = _resolve_type_from_text(text)
    if type_ctx.has_context:
        return type_ctx

    return ProductContext(source="none")


def ask_product_context_message() -> str:
    """Texto pedindo tipo de produto ou modelo antes do diagnóstico."""
    return (
        "Antes de diagnosticar, preciso saber o tipo de produto "
        "(ex.: liquidificador, ventilador, batedeira) ou o modelo "
        "(ex.: BLSTMG-BR8, VTE-02). Você sabe informar um desses? "
        "Com isso busco só nos manuais certos e a resposta fica bem mais assertiva."
    )


def session_continues_diagnosis(session, question: str) -> bool:
    """
    True quando a mensagem atual continua um diagnóstico em aberto
    (ex.: cliente responde só 'cafeteira' após o pedido de tipo/modelo).
    """
    from apps.ai.models import ChatMessage
    from apps.ai.services.confidence import is_fault_symptom

    last_asst = (
        session.messages.filter(role=ChatMessage.Role.ASSISTANT).order_by("-created_at").first()
    )
    if last_asst:
        low = (last_asst.content or "").lower()
        if any(
            marker in low
            for marker in (
                "tipo de produto",
                "descreva o sintoma",
                "preciso saber o tipo",
                "com mais detalhes",
            )
        ):
            return True
        card = last_asst.diagnosis_card or {}
        if card.get("fallback") and card.get("title") in {
            "Qual é o produto?",
            "Preciso de mais detalhes",
        }:
            return True

    q = (question or "").strip()
    ctx = resolve_product_context(q)
    if (
        ctx.has_context
        and ctx.source in {"text_type", "text_model"}
        and not is_fault_symptom(q)
        and len(q.split()) <= 8
        and _prior_fault_from_session(session)
    ):
        return True
    return False


def compose_diagnosis_symptom(session, current: str) -> str:
    """
    Junta o sintoma anterior com a resposta de tipo/modelo do cliente.

    Ex.: 'o produto não liga' + 'cafeteira' →
    'o produto não liga. Tipo/modelo: cafeteira'
    """
    from apps.ai.models import ChatMessage
    from apps.ai.services.confidence import is_fault_symptom

    current = (current or "").strip()
    if not current:
        return current

    prior_users = list(
        session.messages.filter(role=ChatMessage.Role.USER)
        .order_by("created_at")
        .values_list("content", flat=True)[:30]
    )
    prior_fault = ""
    for text in reversed(prior_users):
        t = (text or "").strip()
        if t and is_fault_symptom(t):
            prior_fault = t
            break

    ctx = resolve_product_context(current)
    current_fault = is_fault_symptom(current)

    if ctx.has_context and not current_fault and prior_fault:
        type_bit = current
        if ctx.model_code and ctx.product_type:
            type_bit = f"{ctx.product_type} ({ctx.model_code})"
        elif ctx.model_code:
            type_bit = ctx.model_code
        elif ctx.product_type:
            type_bit = ctx.product_type
        return f"{prior_fault}. Tipo/modelo: {type_bit}"

    if prior_fault and not current_fault and len(current.split()) <= 5:
        # Follow-up curto (ex.: "desde ontem") sem tipo explícito.
        if current.lower() not in prior_fault.lower():
            return f"{prior_fault}. {current}"

    return current


def _prior_fault_from_session(session) -> str:
    from apps.ai.models import ChatMessage
    from apps.ai.services.confidence import is_fault_symptom

    for text in (
        session.messages.filter(role=ChatMessage.Role.USER)
        .order_by("-created_at")
        .values_list("content", flat=True)[:20]
    ):
        t = (text or "").strip()
        if t and is_fault_symptom(t):
            return t
    return ""


def _strip_locale_prefix(text: str) -> str:
    return re.sub(r"^\[Respond in locale=[^\]]+\]\s*", "", text or "", flags=re.I).strip()


def _resolve_model_from_text(text: str) -> ProductContext:
    from apps.catalog.models import EquipmentModel
    from apps.products.models import Product

    candidates: list[str] = []
    for match in _MODEL_CODE_RE.finditer(text):
        code = match.group(1).strip()
        # Evita números soltos / anos
        if code.isdigit() or len(code) < 3:
            continue
        candidates.append(code)

    for code in candidates:
        em = EquipmentModel.objects.filter(code__iexact=code).first()
        if not em:
            em = EquipmentModel.objects.filter(code__icontains=code).order_by("code").first()
        product = (
            Product.objects.filter(
                Q(model_code__iexact=code) | Q(equipment_model__code__iexact=code)
            )
            .select_related("category")
            .first()
        )
        if not product and em:
            product = Product.objects.filter(equipment_model=em).select_related("category").first()
        if product or em:
            return ProductContext(
                product_id=product.pk if product else None,
                category_id=product.category_id if product else None,
                category_name=(product.category.name if product and product.category_id else ""),
                model_code=(em.code if em else (product.model_code if product else code)),
                product_type=(product.category.name if product and product.category_id else ""),
                source="text_model",
            )
        # Só aceita modelo cadastrado — evita pular o pedido de contexto com códigos inventados.

    return ProductContext(source="none")


def _resolve_type_from_text(text: str) -> ProductContext:
    from apps.catalog.models import Category

    low = (text or "").lower()
    cats = list(Category.objects.all().only("id", "name", "slug"))
    for cat in sorted(cats, key=lambda c: len(c.name or ""), reverse=True):
        name = (cat.name or "").strip().lower()
        if len(name) >= 4 and name in low:
            return ProductContext(
                category_id=cat.pk,
                category_name=cat.name,
                product_type=cat.name,
                source="text_type",
            )
        slug_as_words = (cat.slug or "").replace("-", " ").strip().lower()
        if len(slug_as_words) >= 4 and slug_as_words in low:
            return ProductContext(
                category_id=cat.pk,
                category_name=cat.name,
                product_type=cat.name,
                source="text_type",
            )

    for pattern, needle in _TYPE_ALIASES:
        if re.search(rf"\b{pattern}\b", low, flags=re.I):
            cat = Category.objects.filter(name__icontains=needle).first()
            if cat:
                return ProductContext(
                    category_id=cat.pk,
                    category_name=cat.name,
                    product_type=cat.name,
                    source="text_type",
                )
            return ProductContext(product_type=needle, category_name=needle, source="text_type")

    return ProductContext(source="none")
