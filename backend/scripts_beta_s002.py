"""Sessão beta S-002 — OpenAI + R2 contra runserver local."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
sys.path.insert(0, str(Path(__file__).resolve().parent))
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import storages

from apps.ai.models import ChatMessage, ManualChunk, PhotoSearch
from apps.manuals.models import Manual
from apps.notifications.models import EmailLog
from apps.orders.models import Order
from apps.products.models import Product
from apps.tickets.models import Ticket

BASE = os.environ.get("BETA_BASE_URL", "http://127.0.0.1:8000")
User = get_user_model()
results: list[tuple[str, bool, str]] = []


def ok(flow: str, passed: bool, note: str) -> None:
    results.append((flow, passed, note))
    print(f"[{'PASS' if passed else 'FAIL'}] {flow}: {note}")


def csrf_from(session: requests.Session, path: str = "/") -> str:
    r = session.get(f"{BASE}{path}", timeout=30)
    r.raise_for_status()
    m = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)', r.text)
    if m:
        return m.group(1)
    return session.cookies.get("csrftoken", "")


def main() -> int:
    print(
        "=== S-002 prep ===\n"
        f"CHAT={settings.CHAT_LLM_MODE} EMBEDDING={settings.EMBEDDING_MODE} "
        f"PHOTO={settings.PHOTO_LLM_MODE} R2={settings.USE_R2_STORAGE} "
        f"PAYMENT={getattr(settings, 'PAYMENT_PROVIDER', 'mock')}"
    )

    equipment = Product.objects.filter(sku="VTE-02").first()
    part = Product.objects.filter(sku="CAP-35").first()
    manuals = Manual.objects.filter(linked_product=equipment).count() if equipment else 0
    chunks = ManualChunk.objects.filter(product=equipment).count() if equipment else 0
    dims_ok = all(
        c.embedding_dims == settings.EMBEDDING_DIMS
        for c in ManualChunk.objects.filter(product=equipment)
    )

    s = requests.Session()
    home = s.get(f"{BASE}/", timeout=30)
    sw = s.get(f"{BASE}/sw.js", timeout=30)
    cat = s.get(f"{BASE}/catalogo/", params={"q": "CAP-35"}, timeout=30)
    pdp = s.get(f"{BASE}/catalogo/{part.slug}/", timeout=30) if part else None
    has_img = bool(part and part.images.exists())
    ok(
        "1-catalogo",
        bool(
            equipment
            and part
            and manuals
            and chunks >= 1
            and dims_ok
            and cat.status_code == 200
            and "CAP-35" in cat.text
            and pdp
            and pdp.status_code == 200
            and has_img
            and home.status_code == 200
            and sw.status_code == 200
        ),
        f"VTE-02={bool(equipment)} CAP-35={bool(part)} manuals={manuals} chunks={chunks} "
        f"dims_ok={dims_ok} catalog={cat.status_code} pdp={getattr(pdp, 'status_code', None)} "
        f"img={has_img} home={home.status_code} sw={sw.status_code}",
    )

    # --- 2 compra ---
    assert part is not None
    s = requests.Session()
    pdp = s.get(f"{BASE}/catalogo/{part.slug}/", timeout=30)
    csrf = s.cookies.get("csrftoken", "")
    m = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)', pdp.text)
    tok = m.group(1) if m else csrf
    add = s.post(
        f"{BASE}/carrinho/adicionar/",
        data={"product_id": part.pk, "quantity": 1, "csrfmiddlewaretoken": tok},
        headers={
            "Referer": f"{BASE}/catalogo/{part.slug}/",
            "X-CSRFToken": tok,
        },
        timeout=30,
        allow_redirects=True,
    )
    csrf = csrf_from(s, "/checkout/")
    addr = {
        "csrfmiddlewaretoken": csrf,
        "email": "beta.tester@techparts.local",
        "shipping_name": "Beta Tester S002",
        "shipping_phone": "11988887777",
        "shipping_cep": "01310100",
        "shipping_street": "Av Paulista",
        "shipping_number": "1000",
        "shipping_complement": "",
        "shipping_district": "Bela Vista",
        "shipping_city": "São Paulo",
        "shipping_state": "SP",
    }
    r1 = s.post(
        f"{BASE}/checkout/",
        data=addr,
        headers={"Referer": f"{BASE}/checkout/", "X-CSRFToken": csrf},
        timeout=30,
        allow_redirects=True,
    )
    csrf = csrf_from(s, "/checkout/frete/")
    r2 = s.post(
        f"{BASE}/checkout/frete/",
        data={"csrfmiddlewaretoken": csrf, "shipping_option_id": "fixed-econ"},
        headers={"Referer": f"{BASE}/checkout/frete/", "X-CSRFToken": csrf},
        timeout=30,
        allow_redirects=True,
    )
    csrf = csrf_from(s, "/checkout/pagamento/")
    r3 = s.post(
        f"{BASE}/checkout/pagamento/",
        data={"csrfmiddlewaretoken": csrf, "payment_token": "tok_sandbox_4242"},
        headers={"Referer": f"{BASE}/checkout/pagamento/", "X-CSRFToken": csrf},
        timeout=60,
        allow_redirects=True,
    )
    order = (
        Order.objects.filter(email__iexact="beta.tester@techparts.local")
        .order_by("-created_at")
        .first()
    )
    emails = EmailLog.objects.filter(
        kind=EmailLog.Kind.ORDER_CONFIRMATION, status=EmailLog.Status.SENT
    ).count()
    ok(
        "2-compra",
        bool(order and order.status == Order.Status.PAID and emails >= 1),
        f"add={add.status_code} r1={r1.status_code} r2={r2.status_code} r3={r3.status_code} "
        f"order={getattr(order, 'number', None)}/{getattr(order, 'status', None)} emails={emails} "
        f"success_url={'/checkout/sucesso/' in r3.url}",
    )

    # --- 3 chat (OpenAI) ---
    chat = requests.Session()
    chat.get(f"{BASE}/assistente/chat/", timeout=30)
    csrf = chat.cookies.get("csrftoken", "") or csrf_from(chat, "/assistente/chat/")
    stream = chat.post(
        f"{BASE}/assistente/chat/stream/",
        data=json.dumps(
            {
                "question": "Qual o capacitor de partida do VTE-02?",
                "mode": "diagnosis",
                "product_id": equipment.pk if equipment else None,
            }
        ),
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf,
            "Referer": f"{BASE}/assistente/chat/",
        },
        timeout=120,
    )
    body = stream.text
    msg = (
        ChatMessage.objects.filter(role=ChatMessage.Role.ASSISTANT).order_by("-created_at").first()
    )
    has_cite = bool(
        msg
        and (
            msg.sources
            or msg.found_in_manual
            or "capacitor" in (msg.content or "").lower()
            or "CAP-35" in (msg.content or "")
            or "capacitor" in body.lower()
        )
    )
    model_ok = bool(msg and msg.model_name and msg.model_name != "mock-rag")
    ok(
        "3-chat",
        stream.status_code == 200 and has_cite,
        f"stream={stream.status_code} model={getattr(msg, 'model_name', None)} "
        f"found={getattr(msg, 'found_in_manual', None)} "
        f"sources={bool(getattr(msg, 'sources', None))} openai_model={model_ok} "
        f"skus={(getattr(msg, 'diagnosis_card', None) or {}).get('recommendedSkus')} "
        f"snippet={(msg.content or body)[:160].replace(chr(10), ' ') if msg or body else ''}",
    )

    # --- 4 foto (R2 + OpenAI vision) ---
    before_photos = PhotoSearch.objects.count()
    csrf = chat.cookies.get("csrftoken", "")
    jpeg = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        + b"\xff\xdb\x00C\x00"
        + bytes([8] * 64)
        + b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        + b"\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00\x00\x08"
        + b"\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00\x00\x00"
        + b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x7f\xff\xd9"
    )
    photo = chat.post(
        f"{BASE}/assistente/foto/",
        files={"photo": ("peca-s002.jpg", jpeg, "image/jpeg")},
        data={"csrfmiddlewaretoken": csrf},
        headers={
            "X-CSRFToken": csrf,
            "Referer": f"{BASE}/assistente/foto/",
            "HX-Request": "true",
        },
        timeout=120,
    )
    search = PhotoSearch.objects.order_by("-created_at").first()
    storage = storages["default"]
    r2_ok = False
    image_name = ""
    if search and search.image.name:
        image_name = search.image.name
        try:
            r2_ok = storage.exists(image_name) and image_name.startswith("photos/")
        except Exception as exc:  # noqa: BLE001
            r2_ok = False
            image_name = f"err:{exc}"
    empty_ui = "tp-empty" in photo.text or photo.status_code in (200, 202)
    ok(
        "4-foto",
        photo.status_code in (200, 202) and PhotoSearch.objects.count() > before_photos and r2_ok,
        f"status={photo.status_code} search={getattr(search, 'pk', None)} "
        f"r2={r2_ok} key={image_name} model={getattr(search, 'model_name', None)} "
        f"candidates={len(getattr(search, 'candidates', None) or [])} "
        f"ui_ok={empty_ui}",
    )

    # --- 5 chamado ---
    t = requests.Session()
    csrf = csrf_from(t, "/chamados/")
    tpost = t.post(
        f"{BASE}/chamados/",
        data={
            "csrfmiddlewaretoken": csrf,
            "email": "beta.tester@techparts.local",
            "title": "Beta S-002 — capacitor VTE-02 (OpenAI)",
            "equipment": "Mondial VTE-02",
            "description": "Sessão S-002: chat OpenAI citou CAP-35; foto enviada ao R2.",
            "priority": "medium",
        },
        headers={"Referer": f"{BASE}/chamados/"},
        timeout=30,
        allow_redirects=True,
    )
    ticket = (
        Ticket.objects.filter(email__iexact="beta.tester@techparts.local")
        .order_by("-created_at")
        .first()
    )
    events = ticket.events.count() if ticket else 0
    ok(
        "5-chamado",
        bool(ticket and events >= 1),
        f"http={tpost.status_code} code={getattr(ticket, 'code', None)} events={events} "
        f"url={tpost.url}",
    )

    # --- 6 dashboard ---
    from django.test import Client, override_settings

    staff = User.objects.get(username="beta.staff@techparts.local")
    with override_settings(ALLOWED_HOSTS=["*", "testserver", "localhost", "127.0.0.1"]):
        c = Client(HTTP_HOST="127.0.0.1")
        c.force_login(staff)
        dash = c.get("/dashboard/")
        mon = c.get("/dashboard/monitoramento/")
    ok(
        "6-dashboard",
        dash.status_code == 200 and mon.status_code == 200 and b"tp-stat" in dash.content,
        f"insights={dash.status_code} mon={mon.status_code} tp_stat={b'tp-stat' in dash.content}",
    )

    print("\n=== RESUMO S-002 ===")
    passed = sum(1 for _, p, _ in results if p)
    print(f"{passed}/{len(results)} fluxos OK")
    for flow, p, note in results:
        print(f"  - {flow}: {'ok' if p else 'FALHOU'} — {note[:160]}")

    # Persist machine-readable notes for the report updater
    out = Path(__file__).resolve().parent / "scripts_beta_s002_results.json"
    out.write_text(
        json.dumps(
            {
                "passed": passed,
                "total": len(results),
                "modes": {
                    "CHAT_LLM_MODE": settings.CHAT_LLM_MODE,
                    "EMBEDDING_MODE": settings.EMBEDDING_MODE,
                    "PHOTO_LLM_MODE": settings.PHOTO_LLM_MODE,
                    "USE_R2_STORAGE": settings.USE_R2_STORAGE,
                    "PAYMENT_PROVIDER": getattr(settings, "PAYMENT_PROVIDER", "mock"),
                },
                "flows": [{"flow": f, "ok": p, "note": n} for f, p, n in results],
                "order": getattr(order, "number", None),
                "ticket": getattr(ticket, "code", None),
                "chat_model": getattr(msg, "model_name", None),
                "photo_key": image_name,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"results -> {out}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
