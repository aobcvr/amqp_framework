import traceback
from typing import Union

from amqp_framework.http_status import HTTPStatus
from amqp_framework.config import settings
from amqp_framework.exc import APIException


class Response:
    def __init__(self, status: Union[HTTPStatus, int], headers: dict = None, data=None):
        self._status = isinstance(status, HTTPStatus) and status.value or HTTPStatus(status)

        if data is None:
            self.data = {}
        else:
            assert isinstance(data, dict), 'Unsupported type {0} for data, dict required.' \
                .format(type(data))
            self.data = data

        if not headers:
            headers = {}
        assert 'status' not in headers, "The status is automatically record in the headers, " \
                                        "you don't need to override it."
        self.headers = {
            **headers,
            'status': status,
        }

    def __repr__(self):
        return "<Response(status='{0}', data='{1}', headers='{2}')>".format(
            self._status, self.data, self.headers
        )

    @classmethod
    def from_exc(cls, status: Union[HTTPStatus, int], exc: APIException, headers: dict = None, data=None):
        assert isinstance(exc, APIException), 'Exception must inherit from `APIException` base class.'
        if not data:
            data = {}

        data.update({
            getattr(exc, 'code'): getattr(exc, 'default_detail'),
        })

        if settings.DEBUG:
            data.update({
                'traceback': traceback.format_exc()
            })

        return cls(status=status, headers=headers, data=data)
