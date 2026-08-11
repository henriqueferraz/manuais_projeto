"""Validação de upload de manuais (MIME, tamanho, antivírus stub)."""

from __future__ import annotations

from dataclasses import dataclass

import filetype
from django.conf import settings
from django.core.exceptions import ValidationError

# Assinatura EICAR (teste de antivírus) — rejeitar se presente
EICAR_SIGNATURE = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR"


@dataclass(frozen=True)
class ValidatedUpload:
    content: bytes
    mime_type: str
    filename: str
    size_bytes: int
    scan_status: str = "skipped"


def _max_bytes() -> int:
    return int(getattr(settings, "MANUAL_MAX_UPLOAD_BYTES", 25 * 1024 * 1024))


def _allowed_mimes() -> set[str]:
    return set(
        getattr(
            settings,
            "MANUAL_ALLOWED_MIME_TYPES",
            {"application/pdf"},
        )
    )


def sniff_mime(content: bytes, filename: str = "") -> str:
    """Detecta MIME via magic bytes (filetype) + extensão."""
    kind = filetype.guess(content)
    if kind is not None:
        return kind.mime
    lower = filename.lower()
    if lower.endswith(".pdf") and content[:4] == b"%PDF":
        return "application/pdf"
    if content[:4] == b"%PDF":
        return "application/pdf"
    return "application/octet-stream"


def scan_antivirus(content: bytes) -> str:
    """
    Varredura antivírus antes do pipeline.
    - Sempre rejeita assinatura EICAR (teste).
    - Se MANUAL_CLAMAV_ENABLED e clamd disponível, usa clamav.
    - Caso contrário: 'skipped' em DEBUG / stub limpo.
    """
    if EICAR_SIGNATURE in content:
        raise ValidationError("Arquivo rejeitado pela varredura antivírus (assinatura maliciosa).")

    if getattr(settings, "MANUAL_CLAMAV_ENABLED", False):
        try:
            import clamd  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ValidationError("CLAMAV habilitado mas pacote 'clamd' não instalado.") from exc
        try:
            # django-environ/dotenv podem incluir comentário inline no valor
            host = (getattr(settings, "CLAMAV_HOST", "") or "").split("#", 1)[0].strip()
            port = int(getattr(settings, "CLAMAV_PORT", 3310) or 3310)
            if host:
                cd = clamd.ClamdNetworkSocket(host=host, port=port)
            else:
                cd = clamd.ClamdUnixSocket()
            result = cd.instream(content)
            status = result.get("stream", ("ERROR", "unknown"))[0]
            if status == "FOUND":
                raise ValidationError("Arquivo rejeitado pela varredura ClamAV.")
            if status != "OK":
                raise ValidationError(f"Falha na varredura ClamAV: {status}")
            return "clean"
        except ValidationError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ValidationError(f"Erro ao contactar ClamAV: {exc}") from exc

    # Stub: em produção sem ClamAV, ainda bloqueamos EICAR; resto passa como skipped
    if getattr(settings, "DEBUG", False) or getattr(settings, "MANUAL_AV_STUB_OK", True):
        return "skipped"
    return "clean"


def validate_manual_upload(content: bytes, filename: str) -> ValidatedUpload:
    """Valida MIME, tamanho e antivírus. Levanta ValidationError se hostil."""
    if not content:
        raise ValidationError("Arquivo vazio.")

    max_bytes = _max_bytes()
    if len(content) > max_bytes:
        raise ValidationError(
            f"Arquivo excede o tamanho máximo de {max_bytes // (1024 * 1024)} MB."
        )

    mime = sniff_mime(content, filename)
    allowed = _allowed_mimes()
    if mime not in allowed:
        raise ValidationError(
            f"Tipo de arquivo não permitido ({mime}). Aceitos: {', '.join(sorted(allowed))}."
        )

    if not filename.lower().endswith(".pdf"):
        raise ValidationError("Apenas arquivos .pdf são aceitos.")

    scan_status = scan_antivirus(content)
    return ValidatedUpload(
        content=content,
        mime_type=mime,
        filename=filename,
        size_bytes=len(content),
        scan_status=scan_status,
    )
