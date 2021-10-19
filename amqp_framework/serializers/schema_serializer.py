import json
import marshmallow.types

from amqp_framework.serializers.base import BaseSerializer


class SchemaSerializer(BaseSerializer):
    def __init__(
            self,
            data: bytes,
            schema: marshmallow.Schema,
            **kwargs,
    ):
        super().__init__(data=data)
        self.schema = schema
        self.kwargs = kwargs

    def run_validation(self, data: bytes) -> dict:
        try:
            self.schema.load(
                json.loads(data),
                **self.kwargs,
            )
        except marshmallow.exceptions.ValidationError as e:

