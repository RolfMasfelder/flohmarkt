from django.contrib import admin

from project.core.models import (
    Bild,
    BildSymbol,
    Kategorie,
    PPOption,
    Plattform,
    PlatformStatus,
    Artikel,
)


@admin.register(Plattform)
class PlattformAdmin(admin.ModelAdmin):
    list_display = ["name", "adapter_slug", "is_aktiv"]
    list_filter = ["is_aktiv"]


@admin.register(PPOption)
class PPOptionAdmin(admin.ModelAdmin):
    list_display = ["bezeichnung", "kosten", "is_default"]
    list_editable = ["is_default"]


@admin.register(Kategorie)
class KategorieAdmin(admin.ModelAdmin):
    list_display = ["name", "parent"]


@admin.register(BildSymbol)
class BildSymbolAdmin(admin.ModelAdmin):
    list_display = ["bezeichnung", "pfad"]


class BildInline(admin.TabularInline):
    model = Bild
    extra = 0
    fields = ["source", "symbol", "pfad", "alt_text", "position", "is_primary"]


class PlatformStatusInline(admin.TabularInline):
    model = PlatformStatus
    extra = 0
    fields = ["platform", "status", "externe_id", "letzte_sync", "letzte_fehlermeldung"]


@admin.register(Artikel)
class ArtikelAdmin(admin.ModelAdmin):
    list_display = ["titel", "preis", "zustand", "verkauft", "rest_verfügbar", "created_at"]
    list_filter = ["zustand", "verkauft", "kategorie"]
    search_fields = ["titel", "beschreibung"]
    inlines = [BildInline, PlatformStatusInline]
    date_hierarchy = "created_at"
