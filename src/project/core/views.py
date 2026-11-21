"""HTMX-UI-Views — V1: Formular-basierte Verwaltung ohne JS-Build-Chain."""

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from project.core.forms import ArtikelForm
from project.core.models import Artikel


class ArtikelListeView(ListView):
    """Alle aktiven (nicht 'verkauft') Artikel, neueste zuerst."""

    queryset = Artikel.objects.select_related("pp_option", "kategorie")
    template_name = "core/artikel_liste.html"
    context_object_name = "artikel_list"


class ArtikelDetailView(DetailView):
    queryset = Artikel.objects.select_related("pp_option", "kategorie").prefetch_related(
        "bilder__symbol", "plattformstatus_set__platform"
    )
    template_name = "core/artikel_detail.html"
    context_object_name = "artikel"


class ArtikelAnlegenView(SuccessMessageMixin, CreateView):
    model = Artikel
    form_class = ArtikelForm
    template_name = "core/artikel_anlegen.html"
    success_url = reverse_lazy("core:artikel-liste")
    success_message = "Artikel angelegt. 🥕"


class ArtikelBearbeitenView(UpdateView):
    queryset = Artikel.objects.all()
    form_class = ArtikelForm
    template_name = "core/artikel_bearbeiten.html"

    def get_success_url(self):
        return self.get_object().get_absolute_url() if hasattr(self.get_object(), "get_absolute_url") else self.get_object().pk
