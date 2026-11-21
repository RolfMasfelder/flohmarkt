"""Basisdaten seeden: Standard-P&P-Optionen + Beispiel-Plattform.

Idempotent — mehrfache Ausführung ist sicher.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from project.core.models import PPOption, Plattform


class Command(BaseCommand):
    help = "Legt Standard-P&P-Optionen (inkl. 0-€-Default) und Beispiel-Plattform an."

    @staticmethod
    def _set_default(obj: PPOption, was_created: bool) -> None:
        """Genau eine Default-Option: wenn 'Selbstabholung' neu ist, Default setzen."""
        if was_created:
            PPOption.objects.filter(is_default=True, pk__ne=obj.pk).update(is_default=False)
            obj.is_default = True
            obj.save(update_fields=["is_default"])

    def handle(self, *args, **kwargs) -> None:
        with transaction.atomic():
            default, created = PPOption.objects.get_or_create(
                bezeichnung="Selbstabholung",
                defaults={"kosten": Decimal("0.00")},
            )
            self._set_default(default, created)
            if created:
                self.stdout.write(self.style.SUCCESS("✓ Selbstabholung (0 €) angelegt [default]"))

            PPOption.objects.get_or_create(
                bezeichnung="Paket",
                defaults={"kosten": Decimal("3.99"), "beschreibung": "Standardpaket, 0,5–20 kg"},
            )
            PPOption.objects.get_or_create(
                bezeichnung="Maxi-Paket",
                defaults={"kosten": Decimal("8.99"), "beschreibung": "Großformat / sperriges Gut"},
            )
            self.stdout.write(self.style.SUCCESS("✓ P&P-Optionen geprüft/angelegt"))

            plat, created = Plattform.objects.get_or_create(
                name="Kleinanzeigen",
                defaults={
                    "adapter_slug": "kleinanzeigen",
                    "is_aktiv": True,
                    "konfiguration": {"basis_url": "https://www.kleinanzeigen.de"},
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS("✓ Beispiel-Plattform 'Kleinanzeigen' angelegt"))

            self.stdout.write(self.style.SUCCESS("Seed abgeschlossen."))
