from amqp_framework.http_status import HTTPStatus


class AMQPFrameworkError(Exception):
    pass


class ImproperlyConfigured(AMQPFrameworkError):
    pass


class APIException(AMQPFrameworkError):
    """
    Base class for AMQP framework exceptions.
    Subclasses should provide `.status_code` and `.default_detail` properties.
    """
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_detail = HTTPStatus.INTERNAL_SERVER_ERROR.phrase
    default_code = 'error'

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        self.detail = detail
        self.code = code

    def __str__(self):
        return str(self.detail)


class ValidationError(APIException):
    status_code = HTTPStatus.BAD_REQUEST
    default_detail = HTTPStatus.BAD_REQUEST.phrase
    default_code = 'invalid'
