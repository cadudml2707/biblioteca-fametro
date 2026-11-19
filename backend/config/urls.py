from django.urls import include, path


urlpatterns = [
    path("api/v1/", include("apps.usuarios.urls")),
    path("api/v1/", include("apps.obras.urls")),
    path("api/v1/", include("apps.exemplares.urls")),
    path("api/v1/", include("apps.configuracao_biblioteca.urls")),
    path("api/v1/", include("apps.reservas.urls")),
    path("api/v1/", include("apps.emprestimos.urls")),
]
