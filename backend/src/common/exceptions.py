from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_code = "error"
        if response.status_code == 400:
            error_code = "validation_error"
        elif response.status_code == 401:
            error_code = "unauthorized"
        elif response.status_code == 403:
            error_code = "forbidden"
        elif response.status_code == 404:
            error_code = "not_found"
        elif response.status_code == 429:
            error_code = "rate_limited"

        data = response.data
        if isinstance(data, dict) and "detail" in data:
            message = str(data["detail"])
            details = None
        elif isinstance(data, dict):
            message = "Validation failed"
            details = data
        else:
            message = str(data)
            details = None

        response.data = {
            "error": error_code,
            "message": message,
        }
        if details:
            response.data["details"] = details

    return response
