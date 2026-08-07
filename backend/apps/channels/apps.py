from django.apps import AppConfig


class ChannelsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.channels"
    label = "channels_app"  # evita conflito com django.channels
    verbose_name = "Canais (WhatsApp)"
