from rest_framework.exceptions import APIException


class TourError(APIException):
    def __init__(self, code, message, status=422):
        self.status_code = status
        self.default_code = code
        super().__init__(message, code)


def require(condition, code, message, status=422):
    if not condition:
        raise TourError(code, message, status)
