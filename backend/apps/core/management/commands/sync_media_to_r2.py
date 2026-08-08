"""Sobe arquivos locais de MEDIA_ROOT (+ branding opcional) para o Cloudflare R2."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from apps.core.branding import HOME_CAT_HVAC_KEY, HOME_CAT_KITCHEN_KEY, HOME_HERO_KEY
from apps.manuals.storage import use_r2

BRANDING_LOCAL = {
    HOME_HERO_KEY: "home-hero.jpg",
    HOME_CAT_HVAC_KEY: "home-cat-hvac.jpg",
    HOME_CAT_KITCHEN_KEY: "home-cat-kitchen.jpg",
}


class Command(BaseCommand):
    help = "Envia media/ local e assets de branding para o bucket R2 (mesmas keys)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--branding-dir",
            type=str,
            default="",
            help="Pasta local com home-*.jpg (padrão: static/img se existir)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Só lista o que seria enviado",
        )

    def handle(self, *args, **options):
        if not use_r2():
            raise CommandError("USE_R2_STORAGE=false — ative no .env antes de sincronizar.")

        media_root = Path(settings.MEDIA_ROOT)
        uploads: list[tuple[str, Path]] = []
        if media_root.is_dir():
            for path in media_root.rglob("*"):
                if path.is_file():
                    uploads.append((path.relative_to(media_root).as_posix(), path))

        branding_dir = (
            Path(options["branding_dir"])
            if options["branding_dir"]
            else (Path(settings.BASE_DIR) / "static" / "img")
        )
        if branding_dir.is_dir():
            for key, name in BRANDING_LOCAL.items():
                path = branding_dir / name
                if path.is_file():
                    uploads.append((key, path))

        if not uploads:
            self.stdout.write(self.style.WARNING("Nenhum arquivo local para enviar."))
            return

        client = default_storage.connection.meta.client
        bucket = settings.R2_BUCKET_NAME
        ok = fail = 0
        for key, path in uploads:
            if options["dry_run"]:
                self.stdout.write(f"DRY {key} <- {path}")
                continue
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            try:
                with path.open("rb") as fh:
                    client.put_object(
                        Bucket=bucket,
                        Key=key,
                        Body=fh.read(),
                        ContentType=content_type,
                        CacheControl="max-age=86400",
                    )
                self.stdout.write(self.style.SUCCESS(f"OK {key}"))
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(self.style.ERROR(f"FAIL {key}: {exc}"))
                fail += 1

        if options["dry_run"]:
            self.stdout.write(f"Dry-run: {len(uploads)} arquivo(s).")
        else:
            self.stdout.write(self.style.SUCCESS(f"Concluído ok={ok} fail={fail}"))
