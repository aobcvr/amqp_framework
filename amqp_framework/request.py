import aio_pika


class Request:
    """
    Contains AMQP IncomingMessage and Exchange instances.
    """
    def __init__(self, exchange: aio_pika.Exchange, message: aio_pika.IncomingMessage):
        self.exchange = exchange
        self.message = message

    @property
    def headers(self):
        return self.message.headers

    @property
    def body(self):
        return self.message.body
