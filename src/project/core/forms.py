from django import forms
from project.core.models import Artikel


class ArtikelForm(forms.ModelForm):
    """Anlegen & Bearbeiten — V1 minimal.

    Bildauswahl (upload vs. Symbolbild) folgt in einem eigenen Formular/
    Schritt; hier nur die Basisfelder.
    """

    class Meta:
        model = Artikel
        fields = [
            "titel",
            "beschreibung",
            "kategorie",
            "zustand",
            "anzahl_verfügbar",
            "preis",
            "pp_option",
        ]
