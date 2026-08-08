"""Smoke de integrações live em staging (T-P.4) — não chama APIs no CI."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Verifica configuração das integrações live (pagamento, NF-e, frete, "
        "WhatsApp, LLM, assinatura). Não realiza cobranças reais."
    )

    def handle(self, *args, **options):
        rows = [
            ("PAYMENT_PROVIDER", getattr(settings, "PAYMENT_PROVIDER", "mock")),
            ("NFE_PROVIDER", getattr(settings, "NFE_PROVIDER", "mock")),
            ("MELHOR_ENVIO_ENABLED", getattr(settings, "MELHOR_ENVIO_ENABLED", False)),
            ("MELHOR_ENVIO_STUB", getattr(settings, "MELHOR_ENVIO_STUB", False)),
            ("WHATSAPP_MODE", getattr(settings, "WHATSAPP_MODE", "mock")),
            ("CHAT_LLM_MODE", getattr(settings, "CHAT_LLM_MODE", "mock")),
            ("EMBEDDING_MODE", getattr(settings, "EMBEDDING_MODE", "mock")),
            ("DIAGNOSIS_LLM_MODE", getattr(settings, "DIAGNOSIS_LLM_MODE", "mock")),
            ("PHOTO_LLM_MODE", getattr(settings, "PHOTO_LLM_MODE", "mock")),
            ("EXTRACTION_LLM_MODE", getattr(settings, "EXTRACTION_LLM_MODE", "mock")),
            (
                "SUBSCRIPTION_BILLING_MODE",
                getattr(settings, "SUBSCRIPTION_BILLING_MODE", "mock"),
            ),
        ]
        self.stdout.write("=== Smoke T-P.4 — modos atuais ===")
        for key, val in rows:
            self.stdout.write(f"  {key}={val}")

        secrets = {
            "STRIPE_SECRET_KEY": bool(getattr(settings, "STRIPE_SECRET_KEY", "")),
            "MERCADOPAGO_ACCESS_TOKEN": bool(getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", "")),
            "FOCUSNFE_TOKEN": bool(getattr(settings, "FOCUSNFE_TOKEN", "")),
            "MELHOR_ENVIO_TOKEN": bool(getattr(settings, "MELHOR_ENVIO_TOKEN", "")),
            "WHATSAPP_ACCESS_TOKEN": bool(getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")),
            "OPENAI_API_KEY": bool(getattr(settings, "OPENAI_API_KEY", "")),
            "R2_ACCESS_KEY_ID": bool(getattr(settings, "R2_ACCESS_KEY_ID", "")),
            "R2_SECRET_ACCESS_KEY": bool(getattr(settings, "R2_SECRET_ACCESS_KEY", "")),
            "R2_BUCKET_NAME": bool(getattr(settings, "R2_BUCKET_NAME", "")),
        }
        self.stdout.write(f"USE_R2_STORAGE={getattr(settings, 'USE_R2_STORAGE', False)}")
        self.stdout.write("=== Credenciais presentes (bool) ===")
        for key, present in secrets.items():
            self.stdout.write(f"  {key}: {'yes' if present else 'no'}")

        from apps.checkout.shipping import calculate_shipping

        opts = calculate_shipping(cep="01310100", subtotal=Decimal("50.00"))
        self.stdout.write(f"Frete opções: {len(opts)} (fonte={opts[0].source})")
        self.stdout.write(self.style.SUCCESS("Smoke T-P.4 concluído (CI-safe)."))
        self.stdout.write("Docs: docs/adr/0009–0011, docs/deploy.md")
