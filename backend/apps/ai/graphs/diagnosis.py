"""Grafo LangGraph: relato → buscas em paralelo → causa/peça (F6 / Senac Fase A).

Parada: `ask_product` / `ask_details` vão a END; `suggest` encerra o fluxo.
`recursion_limit` em `run_diagnosis` evita loop indefinido.
Fan-out: após `suggest`, `emit_trace` ∥ `emit_done` (paralelização simples, sem ORM).
Tools RAG e pedidos em `search_context` (mesma thread — SQLite/CI).
"""

from __future__ import annotations

import re
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from apps.ai.graphs.state import DiagnosisState
from apps.ai.graphs.tools import retrieve_manual_chunks, search_user_orders

DIAGNOSIS_RECURSION_LIMIT = 8

_DETAIL_HINTS = re.compile(
    r"\b(barulho|ru[ií]do|n[aã]o liga|n[aã]o gira|esquenta|cheiro|"
    r"capacitor|p[aá]|motor|vibra|faz|quebrou|parou|falha|erro)\b",
    re.I,
)
_ORDER_HINTS = re.compile(r"\b(pedido|compra|encomenda|rastreio|entrega)\b", re.I)
_SHORT_RE = re.compile(r"^.{0,12}$")


def _route_decision(
    state: DiagnosisState,
) -> Literal["ask_product", "ask_details", "orders", "manual"]:
    from apps.ai.services.product_context import resolve_product_context

    ctx = resolve_product_context(
        state.get("symptom") or "",
        product_id=state.get("product_id"),
        category_id=state.get("category_id"),
    )
    # Sem tipo/modelo → pergunta antes de qualquer busca ou diagnóstico.
    if not ctx.has_context:
        return "ask_product"

    symptom = (state.get("symptom") or "").strip()
    if _SHORT_RE.match(symptom) or not _DETAIL_HINTS.search(symptom):
        if len(symptom.split()) < 3:
            return "ask_details"
    if _ORDER_HINTS.search(symptom) and state.get("user_id"):
        return "orders"
    return "manual"


def understand_node(state: DiagnosisState) -> dict[str, Any]:
    from apps.ai.services.product_context import (
        ask_product_context_message,
        resolve_product_context,
    )

    ctx = resolve_product_context(
        state.get("symptom") or "",
        product_id=state.get("product_id"),
        category_id=state.get("category_id"),
    )
    decision = _route_decision(state)
    out: dict[str, Any] = {
        "decision": decision,
        "product_id": ctx.product_id or state.get("product_id"),
        "category_id": ctx.category_id or state.get("category_id"),
        "category_name": ctx.category_name,
        "product_type": ctx.product_type,
        "model_code": ctx.model_code,
    }
    if decision in {"ask_product", "ask_details"}:
        if decision == "ask_product":
            out["ask_message"] = ask_product_context_message()
        else:
            out["ask_message"] = (
                "Para diagnosticar com precisão, descreva o sintoma com mais detalhes: "
                "o que acontece (barulho, não liga, vibração) e desde quando. "
                "Com isso busco no manual e sugiro a peça."
            )
        out["answer"] = out["ask_message"]
        out["confidence"] = 0.2
        out["found_in_manual"] = False
        out["recommended_skus"] = []
        out["ref_manual"] = ""
        out["sources"] = []
        out["cause"] = ""
        out["model_name"] = "langgraph-diagnosis-mock"
    return out


def search_context_node(state: DiagnosisState) -> dict[str, Any]:
    """
    Tools RAG + pedidos na mesma thread (SQLite/CI não suporta ORM paralelo).

    O fan-out paralelo do grafo é este node ∥ ``emit_trace``.
    """
    manual = retrieve_manual_chunks(
        {
            "symptom": state.get("symptom") or "",
            "product_id": state.get("product_id"),
            "category_id": state.get("category_id"),
            "category_name": state.get("category_name") or state.get("product_type") or "",
            "model_code": state.get("model_code") or "",
        }
    )
    orders = search_user_orders({"user_id": state.get("user_id")})
    chunks = manual.get("chunks") or []
    errors = list(manual.get("tool_errors") or []) + list(orders.get("tool_errors") or [])
    return {
        "chunks": chunks,
        "sources": chunks,
        "found_in_manual": bool(chunks),
        "orders_summary": orders.get("orders_summary") or "",
        "tool_errors": errors,
    }


def emit_trace_node(state: DiagnosisState) -> dict[str, Any]:
    """Node irmão no fan-out: log estruturado sem I/O de banco."""
    import time

    import structlog

    started = int(time.time() * 1000)
    structlog.get_logger(__name__).info(
        "diagnosis_graph_fanout",
        decision=state.get("decision") or "",
        has_user=bool(state.get("user_id")),
        search_started_ms=started,
    )
    return {"search_started_ms": started}


def suggest_node(state: DiagnosisState) -> dict[str, Any]:
    from django.conf import settings

    from apps.ai.services.confidence import (
        answer_confidence,
        evidence_supports_answer,
        floor_grounded_confidence,
        is_fault_symptom,
    )
    from apps.ai.services.sku_recommend import recommend_skus_for_symptom

    chunks = state.get("chunks") or []
    symptom = state.get("symptom") or ""
    fault = is_fault_symptom(symptom)
    model_name = "langgraph-diagnosis-mock"
    if not chunks:
        return {
            "answer": (
                "Não encontrei isso no manual indexado. "
                "Reformule a pergunta ou abra um chamado para atendimento humano."
            ),
            "cause": "",
            "confidence": 0.0,
            "ref_manual": "",
            "recommended_skus": [],
            "found_in_manual": False,
            "sources": [],
            "model_name": model_name,
        }

    grounded_chunks = [
        c
        for c in chunks
        if evidence_supports_answer(
            symptom,
            section=str(c.get("section") or ""),
            content=str(c.get("content") or c.get("excerpt") or ""),
        )
    ]
    if not grounded_chunks:
        return {
            "answer": (
                "Não encontrei no manual um procedimento de diagnóstico para este sintoma. "
                "Os trechos recuperados são preventivos/de uso e não explicam a falha. "
                "Abra um chamado para atendimento humano."
                if fault
                else (
                    "Não encontrei isso no manual indexado. "
                    "Reformule a pergunta ou abra um chamado para atendimento humano."
                )
            ),
            "cause": "",
            "confidence": 0.0,
            "ref_manual": "",
            "recommended_skus": [],
            "found_in_manual": False,
            "sources": [],
            "model_name": model_name,
        }

    best = grounded_chunks[0]
    section = best.get("section") or "Manual"
    page = best.get("page")
    cite = f"{section}" + (f", pág. {page}" if page else "")
    excerpt = (best.get("content") or best.get("excerpt") or "").strip().replace("\n", " ")
    if len(excerpt) > 360:
        excerpt = excerpt[:357] + "..."

    skus = recommend_skus_for_symptom(
        symptom,
        product_id=state.get("product_id"),
        chunk_texts=[c.get("content") or c.get("excerpt") or "" for c in grounded_chunks],
    )
    cause = f"Possível causa relacionada a: {excerpt}" if fault else excerpt[:240]
    orders_note = ""
    if state.get("orders_summary"):
        orders_note = f"\n\nPedidos recentes:\n{state['orders_summary']}"

    prefix = "Diagnóstico com base no manual" if fault else "Com base no manual"
    answer = f"{prefix} ({cite}): {excerpt} Fonte técnica: {cite}.{orders_note}"
    answer = _redact_secrets(answer)
    if skus and fault:
        answer += f" Peças sugeridas: {', '.join(skus)}."

    # T-P.4: DIAGNOSIS_LLM_MODE=openai enriquece a resposta com LLM (CI = mock)
    mode = (getattr(settings, "DIAGNOSIS_LLM_MODE", "mock") or "mock").lower()
    if mode == "openai":
        enriched = _enrich_diagnosis_openai(
            symptom=symptom,
            cite=cite,
            excerpt=excerpt,
            skus=skus if fault else [],
            fault=fault,
        )
        # Trechos já passaram em evidence_supports_answer: NO_EVIDENCE do LLM
        # não pode zerar a confiança (mesmo padrão do chat RAG).
        if enriched is None:
            model_name = (
                f"{getattr(settings, 'OPENAI_CHAT_MODEL', 'gpt-4o-mini')}+excerpt-fallback"
            )
        elif enriched:
            low = enriched.lower()
            llm_refused = any(m in low for m in ("não encontrei", "nao encontrei", "no_evidence"))
            if llm_refused:
                # Mantém o trecho do manual já montado em `answer`.
                model_name = (
                    f"{getattr(settings, 'OPENAI_CHAT_MODEL', 'gpt-4o-mini')}+excerpt-fallback"
                )
            else:
                answer = enriched
                cause = enriched[:240]
                model_name = getattr(settings, "OPENAI_CHAT_MODEL", "gpt-4o-mini")

    conf = floor_grounded_confidence(
        answer_confidence(
            best.get("score") or 0,
            question=symptom,
            section=section,
            content=str(best.get("content") or best.get("excerpt") or ""),
        )
    )
    answer = _redact_secrets(answer)
    cause = _redact_secrets(cause)
    return {
        "cause": cause,
        "confidence": conf,
        "ref_manual": cite,
        "recommended_skus": skus if fault else [],
        "answer": answer,
        "found_in_manual": True,
        "model_name": model_name,
        "sources": [
            {
                "chunk_id": c.get("chunk_id"),
                "section": c.get("section"),
                "page": c.get("page"),
                "score": c.get("score"),
                "manual_id": c.get("manual_id"),
                "excerpt": c.get("excerpt"),
            }
            for c in grounded_chunks
        ],
    }


def _enrich_diagnosis_openai(
    *,
    symptom: str,
    cite: str,
    excerpt: str,
    skus: list[str],
    fault: bool = True,
) -> str | None:
    """
    Reformula resposta com OpenAI sem inventar fora do trecho.

    Retorna:
    - str: resposta grounded
    - None: trecho NÃO responde (só deve recusar se fault=True)
    - "" : falha de API / skip (mantém resposta mock)
    """
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except ImportError:
        return ""

    from django.conf import settings

    api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
    if not api_key:
        return ""
    llm = ChatOpenAI(
        model=getattr(settings, "OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        temperature=0,
        max_tokens=700,
    )
    if fault:
        system = (
            "Você é o motor de diagnóstico da TechParts AI. "
            "Use APENAS o trecho do manual fornecido. Cite a fonte. "
            "Não invente peças fora da lista sugerida. "
            "Instruções preventivas de segurança (ex.: 'antes de ligar, trave a tampa') "
            "NÃO são diagnóstico de falha — nesse caso responda exatamente: NO_EVIDENCE"
        )
        human = (
            f"Sintoma: {symptom}\nFonte: {cite}\nTrecho: {excerpt}\n"
            f"SKUs sugeridos: {', '.join(skus) or 'nenhum'}\n"
            "Se o trecho diagnosticar o sintoma, escreva o diagnóstico "
            "em português citando a fonte. "
            "Se não diagnosticar, responda apenas NO_EVIDENCE."
        )
    else:
        system = (
            "Você é o assistente técnico da TechParts AI. "
            "Use APENAS o trecho do manual fornecido. Cite a fonte. "
            "Responda perguntas de uso, receita e especificação com base no trecho. "
            "Se o trecho for irrelevante para a pergunta, responda exatamente: NO_EVIDENCE"
        )
        human = (
            f"Pergunta: {symptom}\nFonte: {cite}\nTrecho: {excerpt}\n"
            "Se o trecho responder a pergunta, escreva a resposta em português citando a fonte. "
            "Se for irrelevante, responda apenas NO_EVIDENCE."
        )
    try:
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=human)])
        text = getattr(resp, "content", "") or ""
        if isinstance(text, list):
            text = "".join(
                block.get("text", "") if isinstance(block, dict) else str(block) for block in text
            )
        cleaned = str(text).strip()
        if not cleaned or cleaned.upper().startswith("NO_EVIDENCE"):
            return None
        return cleaned
    except Exception:  # noqa: BLE001
        return ""


def _redact_secrets(text: str) -> str:
    """Garante que credenciais de env não vazem na resposta do agente."""
    from django.conf import settings

    out = text or ""
    key = getattr(settings, "OPENAI_API_KEY", "") or ""
    if key and key in out:
        out = out.replace(key, "[REDACTED]")
    return out


def _after_understand(state: DiagnosisState):
    """Para se faltar contexto; senão segue para as tools de busca."""
    decision = state.get("decision") or "manual"
    if decision in {"ask_details", "ask_product"}:
        return END
    return "search_context"


def _after_suggest(_state: DiagnosisState):
    """Paralelização simples: trace de observabilidade ∥ fechamento."""
    return ["emit_trace", "emit_done"]


def emit_done_node(state: DiagnosisState) -> dict[str, Any]:
    """Irmão de ``emit_trace`` no fan-out pós-suggest (sem banco)."""
    return {"graph_fanout_done": True}


def build_diagnosis_graph():
    graph = StateGraph(DiagnosisState)
    graph.add_node("understand", understand_node)
    graph.add_node("search_context", search_context_node)
    graph.add_node("suggest", suggest_node)
    graph.add_node("emit_trace", emit_trace_node)
    graph.add_node("emit_done", emit_done_node)

    graph.add_edge(START, "understand")
    graph.add_conditional_edges("understand", _after_understand)
    graph.add_edge("search_context", "suggest")
    graph.add_conditional_edges("suggest", _after_suggest)
    graph.add_edge("emit_trace", END)
    graph.add_edge("emit_done", END)
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
        },
        {
            "recursion_limit": DIAGNOSIS_RECURSION_LIMIT,
        },
    )
    return result  # type: ignore[return-value]
