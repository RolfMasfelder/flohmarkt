"""Model-Tests: Artikel-Verhalten, Default-P&P, Symbolbilder, Plattformstatus."""

from decimal import Decimal

import pytest

from project.core.models import Bild, BildSource, BildSymbol, PlatformStatus

pytestmark = pytest.mark.django_db


def test_artikel_hat_default_pp_option(artikel, default_pp):
    """Ein frischer Artikel bekommt automatisch die 0-€-Default-Option."""
    assert artikel.pp_option is not None
    assert artikel.pp_option.is_default is True
    assert artikel.pp_kosten == Decimal("0.00")


def test_rest_verfügbar_initial(artikel):
    assert artikel.rest_verfügbar == 3


def test_rest_verfügbar_nach_verkauf(artikel):
    artikel.anzahl_verkauft = 1
    artikel.save()
    assert artikel.rest_verfügbar == 2


def test_symbol_bild_mit_bezug(artikel):
    """Ein 'symbol'-Bild referenziert zwingend ein Symbol (DB-Constraint)."""
    sym = BildSymbol.objects.create(bezeichnung="Teller-Platzhalter", pfad="teller.svg")
    b = Bild.objects.create(
        artikel=artikel, source=BildSource.SYMBOL, symbol=sym, position=0
    )
    assert b.symbol_id == sym.id


def test_symbol_bild_ohne_bezug_fehlt(artikel):
    with pytest.raises(Exception):
        Bild.objects.create(
            artikel=artikel,
            source=BildSource.SYMBOL,
            pfad=None,
            symbol=None,
            position=1,
        )


def test_upload_bild_ohne_symbol_ok(artikel):
    b = Bild.objects.create(
        artikel=artikel, source=BildSource.UPLOAD, pfad="teller-01.jpg", symbol=None, position=0
    )
    assert b.pfad == "teller-01.jpg"


def test_platformstatus_einzig_pro_paar(artikel, plat_kleinanzeigen):
    PlatformStatus.objects.create(artikel=artikel, platform=plat_kleinanzeigen)
    with pytest.raises(Exception):
        PlatformStatus.objects.create(artikel=artikel, platform=plat_kleinanzeigen)


def test_artikel_str(artikel):
    s = str(artikel)
    assert "Vintage" in s
    assert "42.90" in s
