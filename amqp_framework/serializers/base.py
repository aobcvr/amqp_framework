import abc
import typing

from amqp_framework.exc import ValidationError

empty = object()
"""It is required because `None` may be a valid input or output value."""


class BaseSerializer:
    def __init__(self, data: bytes):
        self.initial_data = data
        self._data = empty
        self._validated_data = empty
        self._errors = empty

    @abc.abstractmethod
    def run_validation(self, data: bytes) -> typing.Any:
        ...

    @property
    def data(self):
        if hasattr(self, 'initial_data') and not hasattr(self, '_validated_data'):
            msg = (
                'When a serializer is passed a `data` keyword argument you '
                'must call `.is_valid()` before attempting to access the '
                'serialized `.data` representation.\n'
                'You should either call `.is_valid()` first, '
                'or access `.initial_data` instead.'
            )
            raise AssertionError(msg)
        return self._validated_data

    @property
    def validated_data(self):
        return self.data

    def is_valid(self, raise_exception=False):
        if self._validated_data is empty:
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.detail
            else:
                self._errors = {}

        if self._errors and raise_exception:
            raise ValidationError(self.errors)

        return not bool(self._errors)

    @property
    def errors(self):
        if self._errors is empty:
            msg = 'You must call `.is_valid()` before accessing `.errors`.'
            raise AssertionError(msg)
        return self._errors
