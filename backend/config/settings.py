from datetime import timedelta
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def required_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"A variável de ambiente {name} é obrigatória.")
    return value


def boolean_env(name, default=False):
    value = os.environ.get(name, str(default)).strip().lower()
    if value not in {"true", "false"}:
        raise ImproperlyConfigured(f"A variável {name} deve ser true ou false.")
    return value == "true"


SECRET_KEY = required_env("DJANGO_SECRET_KEY")
DEBUG = boolean_env("DJANGO_DEBUG")
ALLOWED_HOSTS = [host.strip() for host in required_env("DJANGO_ALLOWED_HOSTS").split(",") if host.strip()]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS deve conter ao menos um host.")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "apps.usuarios.apps.UsuariosConfig",
    "apps.obras.apps.ObrasConfig",
    "apps.exemplares.apps.ExemplaresConfig",
    "apps.configuracao_biblioteca.apps.ConfiguracaoBibliotecaConfig",
    "apps.reservas.apps.ReservasConfig",
    "apps.emprestimos.apps.EmprestimosConfig",
    "apps.relatorios.apps.RelatoriosConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": required_env("POSTGRES_DB"),
        "USER": required_env("POSTGRES_USER"),
        "PASSWORD": required_env("POSTGRES_PASSWORD"),
        "HOST": required_env("POSTGRES_HOST"),
        "PORT": required_env("POSTGRES_PORT"),
    }
}
try:
    port = int(DATABASES["default"]["PORT"])
    if not 1 <= port <= 65535:
        raise ValueError
except ValueError as exc:
    raise ImproperlyConfigured("POSTGRES_PORT deve ser uma porta entre 1 e 65535.") from exc

AUTH_USER_MODEL = "usuarios.Usuario"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Manaus"
USE_I18N = True
USE_TZ = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.usuarios.authentication.PlatformJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "EXCEPTION_HANDLER": "apps.usuarios.exceptions.exception_handler",
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
