import abc
import contextvars
import json
import logging
import typing
from functools import partial

import aio_pika.types

from amqp_framework.config import settings
from amqp_framework.response import Response
from amqp_framework.request import Request

logger = logging.getLogger(__name__)

WORKER_OPTIONS_KEY = '__worker_options__'


def options(
        requeue=False,
        reject_on_redelivered=False,
        ignore_processed=False,
):
    """
    Decorator to set options on `process_request` method of your amqp worker.
    :param requeue: Requeue message when exception.
    :param reject_on_redelivered:
        When True message will be rejected only when
        message was redelivered.
    :param ignore_processed: Do nothing if message already processed
    """

    def decorator(func: callable):
        setattr(func, WORKER_OPTIONS_KEY, {
            'requeue': requeue,
            'reject_on_redelivered': reject_on_redelivered,
            'ignore_processed': ignore_processed,
        })
        return func

    return decorator


class AbstractAMQPWorker(abc.ABC):
    exchange = contextvars.ContextVar('exchange')
    message = contextvars.ContextVar('message')

    channel: typing.Optional[aio_pika.Channel]
    queue: typing.Optional[aio_pika.Queue]

    durable: bool = False
    exclusive: bool = False
    timeout: typing.Optional[aio_pika.types.TimeoutType] = None
    auto_delete: bool = False
    arguments: dict = {}
    passive: bool = False

    @property
    @abc.abstractmethod
    def basename(self) -> str:
        ...

    @property
    def queue_name(self):
        return ':'.join([settings.SERVICE_NAME, self.basename])

    @abc.abstractmethod
    async def process_request(self, request: Request):
        ...

    async def pre_process_request(self, exchange: aio_pika.Exchange, message: aio_pika.IncomingMessage):
        self.exchange = exchange
        self.message = message
        async with message.process(**getattr(self.process_request, WORKER_OPTIONS_KEY, {})):
            result = await self.process_request(
                Request(exchange=exchange, message=message)
            )
            if isinstance(result, Response):
                raise ValueError(9)
                await self.publish_response(response=result)
            elif result:
                raise NotImplementedError()

        logger.debug('Successfully processed request #{0}'.format(message.message_id))

    async def publish_response(self, response: Response):
        await self.exchange.publish(
            aio_pika.Message(
                headers=response.headers,
                body=json.dumps(response.data).encode(),
                content_type='application/json',
                correlation_id=self.message.correlation_id,
            ),
            routing_key=self.message.reply_to,
        )

    async def _declare_queue(self):
        return await self.channel.declare_queue(
            name=self.queue_name,
            durable=self.durable,
            exclusive=self.exclusive,
            timeout=self.timeout,
            auto_delete=self.auto_delete,
            arguments=self.arguments,
            passive=self.passive,
        )

    async def consume(self, channel: aio_pika.Channel):
        self.channel = channel
        self.queue = await self._declare_queue()

        await self.queue.consume(partial(
            self.pre_process_request, self.channel.default_exchange)
        )

    def __repr__(self):
        return self.queue_name
