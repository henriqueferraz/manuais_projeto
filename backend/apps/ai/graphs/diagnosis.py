"""Grafo LangGraph: relato → busca → causa/peça (F6 / T-6.1)."""

from __future__ import annotations

import re
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from apps.ai.graphs.state import DiagnosisState

_DETAIL_HINTS = re.compile(
    r"\b(barulho|ru[ií]do|n[aã]o liga|n[aã]o gira|esquenta|cheiro|"
    r"capacitor|p[aá]|motor|vibra|faz|quebrou|parou|falha|erro)\b",
    re.I,
)
_ORDER_HINTS = re.compile(r"\b(pedido|compra|encomenda|rastreio|entrega)\b", re.I)
_SHORT_RE = re.compile(r"^.{0,12}$")


def _route_decision(state: DiagnosisState) -> Literal["ask_details", "orders", "manual"]:
    symptom = (state.get("symptom") or "").strip()
    if _SHORT_RE.match(symptom) or not _DETAIL_HINTS.search(symptom):
        if len(symptom.split()) < 3:
            return "ask_details"
    if _ORDER_HINTS.search(symptom) and state.get("user_id"):
        return "orders"
    return "manual"


def understand_node(state: DiagnosisState) -> dict[str, Any]:
    decision = _route_decision(state)
    out: dict[str, Any] = {"decision": decision}
    if decision == "ask_details":
        out["ask_message"] = (
            "Para diagnosticar com precisão, descreva o sintoma com mais detalhes: "
            "modelo do equipamento, o que acontece (barulho, não liga, vibração) "
            "e desde quando. Com isso busco no manual e sugiro a peça."
        )
        out["answer"] = out["ask_message"]
        out["confidence"] = 0.2
        out["found_in_manual"] = False
        out["recommended_skus"] = []
        out["ref_manual"] = ""
        out["sources"] = []
        out["cause"] = ""
    return out


def search_manual_node(state: DiagnosisState) -> dict[str, Any]:
    from apps.ai.services.retrieval import retrieve

    hits = retrieve(
        state.get("symptom") or "",
        product_id=state.get("product_id"),
        category_id=state.get("category_id"),
    )
    chunks = [
        {
            "chunk_id": h.chunk.pk,
            "section": h.chunk.section,
            "page": h.chunk.page,
            "score": round(h.score, 4),
            "manual_id": h.chunk.manual_id,
            "excerpt": h.chunk.content[:240],
            "content": h.chunk.content,
        }
        for h in hits
    ]
    return {"chunks": chunks, "sources": chunks, "found_in_manual": bool(chunks)}


def search_orders_node(state: DiagnosisState) -> dict[str, Any]:
    from apps.orders.models import Order

    user_id = state.get("user_id")
    if not user_id:
        return {"orders_summary": "", "decision": "manual"}
    orders = (
        Order.objects.filter(user_id=user_id).prefetch_related("items").order_by("-created_at")[:5]
    )
    lines: list[str] = []
    for order in orders:
        skus = ", ".join(i.sku for i in order.items.all()[:6])
        lines.append(f"{order.number} [{order.status}]: {skus or '—'}")
    summary = "\n".join(lines) if lines else "Nenhum pedido recente encontrado."
    # Após checar pedidos, ainda consulta o manual para causa técnica
    return {"orders_summary": summary, "decision": "manual"}


def suggest_node(state: DiagnosisState) -> dict[str, Any]:
    from django.conf import settings

    from apps.ai.services.sku_recommend import recommend_skus_for_symptom

    chunks = state.get("chunks") or []
    symptom = state.get("symptom") or ""
    if not chunks:
        return {
            "answer": (
                "Não encontrei isso no manual indexado. "
                "Reformule o sintoma ou abra um chamado para atendimento humano."
            ),
            "cause": "",
            "confidence": 0.0,
            "ref_manual": "",
            "recommended_skus": [],
            "found_in_manual": False,
            "sources": [],
        }

    best = chunks[0]
    section = best.get("section") or "Manual"
    page = best.get("page")
    cite = f"{section}" + (f", pág. {page}" if page else "")
    excerpt = (best.get("content") or best.get("excerpt") or "").strip().replace("\n", " ")
    if len(excerpt) > 360:
        excerpt = excerpt[:357] + "..."

    skus = recommend_skus_for_symptom(
        symptom,
        product_id=state.get("product_id"),
        chunk_texts=[c.get("content") or c.get("excerpt") or "" for c in chunks],
    )
    cause = f"Possível causa relacionada a: {excerpt}"
    orders_note = ""
    if state.get("orders_summary"):
        orders_note = f"\n\nPedidos recentes:\n{state['orders_summary']}"

    answer = (
        f"Diagnóstico com base no manual ({cite}): {excerpt} "
        f"Fonte técnica: {cite}."
        f"{orders_note}"
    )
    if skus:
        answer += f" Peças sugeridas: {', '.join(skus)}."

    # T-P.4: DIAGNOSIS_LLM_MODE=anthropic enriquece a resposta com LLM (CI = mock)
    mode = (getattr(settings, "DIAGNOSIS_LLM_MODE", "mock") or "mock").lower()
    if mode == "anthropic":
        enriched = _enrich_diagnosis_anthropic(
            symptom=symptom, cite=cite, excerpt=excerpt, skus=skus
        )
        if enriched:
            answer = enriched
            cause = enriched[:240]

    conf = round(min(0.95, float(best.get("score") or 0) + 0.25), 3)
    return {
        "cause": cause,
        "confidence": conf,
        "ref_manual": cite,
        "recommended_skus": skus,
        "answer": answer,
        "found_in_manual": True,
        "sources": [
            {
                "chunk_id": c.get("chunk_id"),
                "section": c.get("section"),
                "page": c.get("page"),
                "score": c.get("score"),
                "manual_id": c.get("manual_id"),
                "excerpt": c.get("excerpt"),
            }
            for c in chunks
        ],
    }


def _enrich_diagnosis_anthropic(*, symptom: str, cite: str, excerpt: str, skus: list[str]) -> str:
    """Opcional: reformula diagnóstico com Anthropic sem inventar fora do trecho."""
    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage
    except ImportError:
        return ""

    from django.conf import settings

    api_key = getattr(settings, "ANTHROPIC_API_KEY", "") or ""
    if not api_key:
        return ""
    llm = ChatAnthropic(
        model=getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        api_key=api_key,
        temperature=0,
        max_tokens=600,
    )
    system = (
        "Você é o motor de diagnóstico da TechParts AI. "
        "Use APENAS o trecho do manual fornecido. Cite a fonte. "
        "Não invente peças fora da lista sugerida."
    )
    human = (
        f"Sintoma: {symptom}\nFonte: {cite}\nTrecho: {excerpt}\n"
        f"SKUs sugeridos: {', '.join(skus) or 'nenhum'}\n"
        "Escreva o diagnóstico em português, citando a fonte."
    )
    try:
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=human)])
        text = getattr(resp, "content", "") or ""
        if isinstance(text, list):
            text = "".join(
                block.get("text", "") if isinstance(block, dict) else str(block) for block in text
            )
        return str(text).strip()
    except Exception:  # noqa: BLE001
        return ""


def _after_understand(state: DiagnosisState) -> str:
    decision = state.get("decision") or "manual"
    if decision == "ask_details":
        return "ask_details"
    if decision == "orders":
        return "orders"
    return "manual"


def build_diagnosis_graph():
    graph = StateGraph(DiagnosisState)
    graph.add_node("understand", understand_node)
    graph.add_node("search_manual", search_manual_node)
    graph.add_node("search_orders", search_orders_node)
    graph.add_node("suggest", suggest_node)

    graph.add_edge(START, "understand")
    graph.add_conditional_edges(
        "understand",
        _after_understand,
        {"ask_details": END, "orders": "search_orders", "manual": "search_manual"},
    )
    graph.add_edge("search_orders", "search_manual")
    graph.add_edge("search_manual", "suggest")
    graph.add_edge("suggest", END)
    return graph.compile()


_COMPILED = None


def get_diagnosis_graph():
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = build_diagnosis_graph()
    return _COMPILED


def run_diagnosis(
    *,
    symptom: str,
    product_id: int | None = None,
    category_id: int | None = None,
    user_id: int | None = None,
) -> DiagnosisState:
    graph = get_diagnosis_graph()
    result = graph.invoke(
        {
            "symptom": symptom,
            "product_id": product_id,
            "category_id": category_id,
            "user_id": user_id,
        }
    )
    return result  # type: ignore[return-value]
