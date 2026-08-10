"""Regras e normalização de fotos de produto (layout 1:1 no catálogo)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError

PRODUCT_IMAGE_MAX_COUNT = 5
PRODUCT_IMAGE_MAX_BYTES = 2 * 1024 * 1024  # 2 MB
PRODUCT_IMAGE_MIN_SIDE = 400
PRODUCT_IMAGE_MAX_SIDE = 800
# Proporção próxima do quadrado (cards usam aspect-ratio 1/1)
PRODUCT_IMAGE_MIN_RATIO = 0.75  # 3:4
PRODUCT_IMAGE_MAX_RATIO = 1.34  # ~4:3
PRODUCT_IMAGE_TARGET_SIDE = 800
PRODUCT_IMAGE_OUTPUT_FORMAT = "JPEG"
PRODUCT_IMAGE_OUTPUT_EXT = ".jpg"
PRODUCT_IMAGE_OUTPUT_MIME = "image/jpeg"
PRODUCT_IMAGE_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
PRODUCT_IMAGE_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
PRODUCT_IMAGE_INPUT_MAX_BYTES = 25 * 1024 * 1024  # limite bruto antes de processar


def validate_product_image(upload: UploadedFile) -> None:
    """Valida se o arquivo já está no padrão (útil em testes / revalidação)."""
    name = getattr(upload, "name", "") or ""
    ext = Path(name).suffix.lower()
    if ext not in PRODUCT_IMAGE_ALLOWED_EXT:
        raise ValidationError("Extensão inválida. Use JPG, JPEG, PNG ou WEBP.")

    content_type = (getattr(upload, "content_type", "") or "").lower()
    if content_type and content_type not in PRODUCT_IMAGE_ALLOWED_MIME:
        raise ValidationError("Tipo de arquivo inválido. Use JPG, PNG ou WEBP.")

    size = getattr(upload, "size", None)
    if size is not None and size > PRODUCT_IMAGE_MAX_BYTES:
        raise ValidationError(
            f"Arquivo muito grande ({size // 1024} KB). Máximo: "
            f"{PRODUCT_IMAGE_MAX_BYTES // (1024 * 1024)} MB."
        )
    if size is not None and size < 1024:
        raise ValidationError("Arquivo de imagem inválido ou vazio.")

    width, height, fmt = _read_image_meta(upload)

    if fmt not in {"JPEG", "PNG", "WEBP"}:
        raise ValidationError("Formato de imagem não suportado. Use JPG, PNG ou WEBP.")

    if width < PRODUCT_IMAGE_MIN_SIDE or height < PRODUCT_IMAGE_MIN_SIDE:
        raise ValidationError(
            f"Imagem muito pequena ({width}×{height}px). "
            f"Mínimo: {PRODUCT_IMAGE_MIN_SIDE}×{PRODUCT_IMAGE_MIN_SIDE}px."
        )
    if width > PRODUCT_IMAGE_MAX_SIDE or height > PRODUCT_IMAGE_MAX_SIDE:
        raise ValidationError(
            f"Imagem muito grande ({width}×{height}px). "
            f"Máximo: {PRODUCT_IMAGE_MAX_SIDE}×{PRODUCT_IMAGE_MAX_SIDE}px."
        )

    ratio = width / height if height else 0
    if ratio < PRODUCT_IMAGE_MIN_RATIO or ratio > PRODUCT_IMAGE_MAX_RATIO:
        raise ValidationError(
            f"Proporção inadequada ({width}×{height}). "
            "Use imagem próxima do quadrado (entre 3:4 e 4:3) para não estourar o layout."
        )


def prepare_product_image(upload: UploadedFile) -> InMemoryUploadedFile:
    """
    Converte o upload para o padrão do catálogo:
    JPEG, ~800×800 (crop central), ≤ 2 MB, proporção entre 3:4 e 4:3.
    """
    from apps.manuals.validators import scan_antivirus

    name = getattr(upload, "name", "") or "foto.jpg"
    ext = Path(name).suffix.lower()
    if ext and ext not in PRODUCT_IMAGE_ALLOWED_EXT:
        raise ValidationError("Extensão inválida. Use JPG, JPEG, PNG ou WEBP.")

    content_type = (getattr(upload, "content_type", "") or "").lower()
    if content_type and content_type not in PRODUCT_IMAGE_ALLOWED_MIME:
        raise ValidationError("Tipo de arquivo inválido. Use JPG, PNG ou WEBP.")

    size = getattr(upload, "size", None)
    if size is not None and size > PRODUCT_IMAGE_INPUT_MAX_BYTES:
        raise ValidationError(
            f"Arquivo muito grande para processar ({size // (1024 * 1024)} MB). "
            "Máximo de envio: 25 MB."
        )
    if size is not None and size < 32:
        raise ValidationError("Arquivo de imagem inválido ou vazio.")

    # Obrigatório: varredura antivírus em todo upload
    upload.seek(0)
    raw_bytes = upload.read()
    upload.seek(0)
    scan_antivirus(raw_bytes)

    try:
        upload.seek(0)
        with Image.open(upload) as raw:
            img = ImageOps.exif_transpose(raw)
            img.load()
            img = _to_rgb(img)
            img = _fit_to_catalog_square(img)
            payload, out_name = _encode_jpeg(img, original_name=name)
        upload.seek(0)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError("Não foi possível ler a imagem. Arquivo corrompido?") from exc

    return InMemoryUploadedFile(
        file=payload,
        field_name="images",
        name=out_name,
        content_type=PRODUCT_IMAGE_OUTPUT_MIME,
        size=payload.getbuffer().nbytes,
        charset=None,
    )


def _read_image_meta(upload: UploadedFile) -> tuple[int, int, str]:
    try:
        upload.seek(0)
        with Image.open(upload) as img:
            img.verify()
        upload.seek(0)
        with Image.open(upload) as img:
            width, height = img.size
            fmt = (img.format or "").upper()
        upload.seek(0)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError("Não foi possível ler a imagem. Arquivo corrompido?") from exc
    return width, height, fmt


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode in {"RGB", "L"}:
        return img.convert("RGB")
    if img.mode in {"RGBA", "LA"} or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    return img.convert("RGB")


def _fit_to_catalog_square(img: Image.Image) -> Image.Image:
    """Crop central para 1:1 e redimensiona para o alvo do catálogo (~800×800)."""
    width, height = img.size
    if width < 1 or height < 1:
        raise ValidationError("Arquivo de imagem inválido ou vazio.")

    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    img = img.crop((left, top, left + side, top + side))
    target = PRODUCT_IMAGE_TARGET_SIDE
    if img.size != (target, target):
        img = img.resize((target, target), Image.Resampling.LANCZOS)
    return img


def _encode_jpeg(img: Image.Image, *, original_name: str) -> tuple[BytesIO, str]:
    stem = Path(original_name).stem or "foto"
    safe_stem = (
        "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in stem).strip("-") or "foto"
    )
    out_name = f"{safe_stem}{PRODUCT_IMAGE_OUTPUT_EXT}"

    for quality in (85, 75, 65, 55, 45):
        buf = BytesIO()
        img.save(buf, format=PRODUCT_IMAGE_OUTPUT_FORMAT, quality=quality, optimize=True)
        if buf.tell() <= PRODUCT_IMAGE_MAX_BYTES:
            buf.seek(0)
            return buf, out_name

    # Último recurso: reduzir um pouco mais e recomprimir.
    smaller = img.resize(
        (PRODUCT_IMAGE_MIN_SIDE, PRODUCT_IMAGE_MIN_SIDE),
        Image.Resampling.LANCZOS,
    )
    buf = BytesIO()
    smaller.save(buf, format=PRODUCT_IMAGE_OUTPUT_FORMAT, quality=40, optimize=True)
    if buf.tell() > PRODUCT_IMAGE_MAX_BYTES:
        raise ValidationError("Não foi possível comprimir a imagem para menos de 2 MB.")
    buf.seek(0)
    return buf, out_name
