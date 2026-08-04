from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cria grupos RBAC iniciais (admin, revisao_catalogo, suporte)."

    def handle(self, *args, **options):
        from django.conf import settings

        created = []
        for name in settings.RBAC_GROUPS:
            group, was_created = Group.objects.get_or_create(name=name)
            if was_created:
                created.append(name)
                self.stdout.write(self.style.SUCCESS(f"Grupo criado: {name}"))
            else:
                self.stdout.write(f"Grupo já existe: {group.name}")

        if not created:
            self.stdout.write("Nenhum grupo novo.")
        else:
            self.stdout.write(self.style.SUCCESS(f"Criados: {', '.join(created)}"))
