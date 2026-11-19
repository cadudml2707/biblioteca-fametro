from django.urls import path

from .views import CancelarReservaView, ConfirmarReservaView, ReservaListCreateView


urlpatterns = [
    path("reservas", ReservaListCreateView.as_view(), name="reservas"),
    path("reservas/<int:pk>/confirmar", ConfirmarReservaView.as_view(), name="confirmar-reserva"),
    path("reservas/<int:pk>/cancelar", CancelarReservaView.as_view(), name="cancelar-reserva"),
]
