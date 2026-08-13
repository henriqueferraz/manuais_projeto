"""Calibração, limiar e groundedness das respostas do agente (chat/diagnóstico)."""

from __future__ import annotations

import re

from django.conf import settings

# Affine score→confiança no modo mock:
# ~0.20 (hit lexical sólido) → ≥70%; ~0.12 (RAG_MIN / fraco) → ~50%.
_SCORE_SCALE_MOCK = 2.5
_SCORE_BIAS_MOCK = 0.20
# OpenAI: hits úteis frequentes ~0.32–0.55; mapear ~0.32 → 70%.
_SCORE_SCALE_OPENAI = 2.0
_SCORE_BIAS_OPENAI = 0.06
_MAX_CONFIDENCE = 0.95

_FAULT_SYMPTOM_RE = re.compile(
    r"\b("
    r"n[aã]o\s+liga|nao\s+liga|n[aã]o\s+gira|nao\s+gira|"
    r"barulho|ru[ií]do|vibra(?:ndo|ção|cao)?|esquenta|cheiro|"
    r"parou|quebrou|falha|defeito|n[aã]o\s+funcion"
    r")\b",
    re.I,
)

# Evidência real de diagnóstico/falha no trecho (não instrução preventiva).
_FAULT_EVIDENCE_RE = re.compile(
    r"("
    r"n[aã]o\s+liga|nao\s+liga|n[aã]o\s+gira|nao\s+gira|"
    r"faz\s+barulho|quando\s+o\s+.+\s+(faz|n[aã]o)|"
    r"problema|solu[cç][aã]o\s+de\s+problema|tabela\s+de\s+solu|"
    r"verifique\s+o\s+capacitor|capacitor\s+de\s+partida|"
    r"causa\s+prov[aá]vel|poss[ií]vel\s+causa"
    r")",
    re.I,
)

_PREVENTIVE_ONLY_RE = re.compile(
    r"("
    r"antes\s+de\s+ligar|"
    r"instru[cç][oõ]es?\s+importantes?\s+de\s+seguran|"
    r"certifique-se\s+de\s+que\s+a\s+tampa|"
    r"mantenha\s+estas\s+instru"
    r")",
    re.I,
)

_STOPWORDS = {
    "a",
    "as",
    "o",
    "os",
    "um",
    "uma",
    "uns",
    "umas",
    "de",
    "da",
    "do",
    "das",
    "dos",
    "e",
    "ou",
    "para",
    "por",
    "com",
    "sem",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "que",
    "se",
    "ao",
    "à",
    "tem",
    "ter",
    "há",
    "como",
    "qual",
    "quais",
    "meu",
    "minha",
    "meus",
    "minhas",
    "este",
    "esta",
    "esse",
    "essa",
    "isto",
    "isso",
    "usar",
    "utilize",
    "utilizar",
    "função",
    "funcao",
    "modo",
    "receita",
    "receitas",
}


def min_answer_confidence() -> float:
    """Mínimo de acertividade para exibir uma resposta (padrão 70%)."""
    return float(getattr(settings, "CHAT_MIN_ANSWER_CONFIDENCE", 0.70))


def is_fault_symptom(question: str) -> bool:
    """True quando a pergunta descreve falha/sintoma (não uso/receita/especificação)."""
    return bool(_FAULT_SYMPTOM_RE.search(question or ""))


def retrieval_to_confidence(score: float) -> float:
    """
    Converte score híbrido de retrieval em acertividade da resposta (0–1).

    - mock: scores típicos ~0.12–0.35 → affine para escala de produto
    - openai: hits úteis ~0.32–0.55 → affine (≈0.32 → ≥70%)
    """
    try:
        raw = float(score)
    except (TypeError, ValueError):
        return 0.0
    mode = getattr(settings, "EMBEDDING_MODE", "mock").lower()
    if mode == "openai":
        return round(
            min(_MAX_CONFIDENCE, max(0.0, raw * _SCORE_SCALE_OPENAI + _SCORE_BIAS_OPENAI)),
            3,
        )
    return round(
        min(_MAX_CONFIDENCE, max(0.0, raw * _SCORE_SCALE_MOCK + _SCORE_BIAS_MOCK)),
        3,
    )


def _term_variants(token: str) -> set[str]:
    """Variantes simples PT (cenoura/cenouras, mamão/mamões)."""
    t = (token or "").lower()
    variants = {t}
    if t.endswith("ões") and len(t) > 4:
        variants.add(t[:-3] + "ão")
    elif t.endswith("ão") and len(t) > 3:
        variants.add(t[:-2] + "ões")
    if t.endswith("ais") and len(t) > 4:
        variants.add(t[:-3] + "al")
    elif t.endswith("al") and len(t) > 3:
        variants.add(t + "is")
    if len(t) > 3 and t.endswith("s") and not t.endswith(("ss", "us", "is")):
        variants.add(t[:-1])
    elif len(t) > 3 and not t.endswith("s"):
        variants.add(t + "s")
    return variants


def _terms_match(q_term: str, doc_terms: set[str]) -> bool:
    variants = _term_variants(q_term)
    if variants & doc_terms:
        return True
    # Substring só com tokens longos (evita "ou" ∈ "cenoura", "as" ∈ "cenouras").
    for doc in doc_terms:
        shorter, longer = (q_term, doc) if len(q_term) <= len(doc) else (doc, q_term)
        if len(shorter) < 5:
            continue
        if shorter in longer and len(shorter) / max(len(longer), 1) >= 0.55:
            return True
    return False


def salient_term_coverage(question: str, text: str) -> float:
    """Fração dos termos relevantes da pergunta presentes no trecho (0–1)."""
    from apps.ai.services.embeddings import tokenize

    q_terms = {t for t in tokenize(question or "") if t not in _STOPWORDS and len(t) > 2}
    if not q_terms:
        return 0.0
    doc_terms = tokenize(text or "")
    matched = sum(1 for t in q_terms if _terms_match(t, doc_terms))
    return matched / len(q_terms)


def answer_confidence(
    score: float,
    *,
    question: str = "",
    section: str = "",
    content: str = "",
) -> float:
    """
    Confiança final da resposta = calibração do score + boost lexical.

    Receitas/títulos (ex.: "MILK SHAKE CREMOSO") costumam ter score híbrido OpenAI
    moderado (~0.35) mesmo com match claro — o boost evita falso "não sei".
    """
    text = f"{section or ''}\n{content or ''}"
    base = retrieval_to_confidence(score)
    if _has_phrase_hit(question, text):
        base = max(base, 0.88)
    coverage = salient_term_coverage(question, text)
    if coverage >= 0.67:
        base = max(base, 0.86)
    elif coverage >= 0.5:
        base = max(base, 0.78)
    elif coverage >= 0.34:
        base = max(base, 0.72)
    return round(min(_MAX_CONFIDENCE, base), 3)


def is_below_answer_threshold(confidence: float) -> bool:
    """True se a confiança está abaixo do mínimo configurável."""
    return float(confidence or 0.0) < min_answer_confidence()


def format_low_confidence_message(ticket_code: str) -> str:
    """Mensagem de recusa + código do chamado aberto automaticamente."""
    pct = int(round(min_answer_confidence() * 100))
    code = (ticket_code or "").strip() or "—"
    return (
        f"Não sei a resposta com segurança suficiente com base no manual indexado "
        f"(confiança abaixo de {pct}%). Não vou inventar uma resposta. "
        f"Abri o chamado {code} para atendimento humano — um especialista vai te ajudar."
    )


def evidence_supports_answer(
    question: str,
    *,
    section: str = "",
    content: str = "",
) -> bool:
    """
    Verifica se o trecho realmente embasa a pergunta/sintoma.

    Evita o falso positivo clássico: seção de segurança preventiva
    ("antes de ligar, trave a tampa") usada como diagnóstico de "não liga".
    """
    body = (content or "").strip()
    if not body:
        return False

    text = f"{section or ''}\n{body}"
    q = question or ""

    # Uso/receita/especificação: exige overlap lexical relevante (não só palavra genérica).
    if not is_fault_symptom(q):
        return _usage_evidence_ok(q, text)

    if not _FAULT_EVIDENCE_RE.search(text):
        return False

    # "Antes de ligar… tampa" não é diagnóstico, mesmo com a palavra "ligar".
    if _PREVENTIVE_ONLY_RE.search(text) and not re.search(
        r"n[aã]o\s+liga|nao\s+liga|n[aã]o\s+gira|problema|quando\s+o\s+",
        text,
        re.I,
    ):
        return False

    # Sintoma da pergunta precisa aparecer no trecho (não ligar ≠ não girar).
    q_faults = {m.group(0).lower() for m in _FAULT_SYMPTOM_RE.finditer(q)}
    doc_faults = {m.group(0).lower() for m in _FAULT_SYMPTOM_RE.finditer(text)}
    if q_faults and doc_faults and q_faults.isdisjoint(doc_faults):
        from apps.ai.services.embeddings import tokenize

        q_toks = tokenize(q)
        d_toks = tokenize(text)
        if "capacitor" in q_toks and "capacitor" in d_toks:
            return True
        return False

    return True


_GENERIC_ALONE = {
    "liquidificador",
    "ventilador",
    "cafeteira",
    "batedeira",
    "aparelho",
    "produto",
    "manual",
    "modelo",
    "instruções",
    "instrucoes",
    "elétrica",
    "eletrica",
}


def _usage_evidence_ok(question: str, text: str) -> bool:
    from apps.ai.services.embeddings import tokenize

    if _has_phrase_hit(question, text):
        return True
    q_terms = {t for t in tokenize(question or "") if t not in _STOPWORDS and len(t) > 2}
    if not q_terms:
        return True
    doc_terms = tokenize(text or "")
    matched = {t for t in q_terms if _terms_match(t, doc_terms)}
    if len(matched) >= 2:
        return True
    if len(matched) == 1:
        term = next(iter(matched))
        if term in _GENERIC_ALONE:
            return False
        return len(term) >= 4
    return False


def _has_phrase_hit(question: str, text: str) -> bool:
    """Match de bi/trigramas relevantes (ex.: 'suco de cenoura', 'milk shake')."""
    from apps.ai.services.embeddings import _TOKEN_RE, tokenize

    q_tokens = [t for t in tokenize(question or "") if t not in _STOPWORDS and len(t) > 2]
    if len(q_tokens) < 2:
        return False
    # Ordem preservada (tokenize() devolve set).
    hay_tokens = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    hay_set = set(hay_tokens)
    hay = " ".join(hay_tokens)
    hay_compact = "".join(hay_tokens)
    hay_stem = hay
    for tok in hay_tokens:
        for v in _term_variants(tok):
            if v != tok:
                hay_stem += f" {v}"
    for n in (3, 2):
        if len(q_tokens) < n:
            continue
        for i in range(0, len(q_tokens) - n + 1):
            span = q_tokens[i : i + n]
            phrase = " ".join(span)
            if phrase in hay or phrase in hay_stem:
                return True
            if "".join(span) in hay_compact:
                return True
            # suco cenoura ↔ suco … cenouras (ordem preservada, gap curto)
            if n == 2 and span[0] in hay_set:
                idx = hay_tokens.index(span[0])
                window = hay_tokens[idx : idx + 6]
                if any(_terms_match(span[1], {w}) for w in window):
                    return True
    return False
