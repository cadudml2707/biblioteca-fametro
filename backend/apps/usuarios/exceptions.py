from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    detail = response.data
    if isinstance(exc, ValidationError):
        response.data = {"codigo": "dados_invalidos", "mensagem": "Confira os dados informados.", "erros": detail}
    else:
        message = detail.get("detail", "Não foi possível concluir a operação.") if isinstance(detail, dict) else str(detail)
        response.data = {"codigo": getattr(exc, "default_code", "erro"), "mensagem": str(message)}
    return response
