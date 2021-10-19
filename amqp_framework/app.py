import aio_pika
import asyncio
import logging
import typing
from aio_pika import connect_robust, RobustConnection

from amqp_framework.config import settings
from amqp_framework.utils.imports import symbol_by_name
from amqp_framework.workers import AbstractAMQPWorker

logger = logging.getLogger(__name__)


class AMQPFramework:
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.workers: typing.List[AbstractAMQPWorker] = []
        self.connection: typing.Optional[aio_pika.RobustConnection] = None
        self.channel: typing.Optional[aio_pika.Channel] = None

    async def initialize(self):
        """Initialize app - connection to channel and declaring workers."""
        self.connection = await self.robust_connection()
        self.channel = self.connection.channel()

        await self.channel.initialize(timeout=5)
        await self.declare_workers()

    async def configure(self, **options):
        settings.configure(**options)

    async def robust_connection(self) -> RobustConnection:
        return await connect_robust(
            url=settings.BROKER_URL,
            loop=self.loop,
            **settings.CONNECTION_OPTIONS
        )

    async def declare_workers(self):
        self.workers = [symbol_by_name(worker)() for worker in settings.WORKERS]

        worker: AbstractAMQPWorker
        for worker in self.workers:
            await worker.consume(channel=self.channel)
            logger.info("Worker '{0}' has been declared.".format(worker))
        logger.info('{0} declared workers.'.format(len(self.workers)))
        print(settings.CONNECTION_OPTIONS)
