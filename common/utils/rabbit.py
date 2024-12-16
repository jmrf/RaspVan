import logging
import os
import time
from typing import Callable, Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel

from common.utils.io import init_logger
from raspvan.constants import (
    DEFAULT_RABBITMQ_HOST,
    DEFAULT_RABBITMQ_PORT,
    RABBITMQ_HOST_ENV_VAR,
    RABBITMQ_PORT_ENV_VAR,
)

logger = logging.getLogger(__name__)
init_logger(level=os.getenv("LOG_LEVEL", logging.INFO), logger=logger)


def get_amqp_uri_from_env():
    rabbit_host = os.getenv(RABBITMQ_HOST_ENV_VAR)
    if rabbit_host is None:
        logger.warning(
            f"🐇 env.var '{RABBITMQ_HOST_ENV_VAR}' not set. "
            f"Defaulting to: '{DEFAULT_RABBITMQ_HOST}'"
        )
        rabbit_host = DEFAULT_RABBITMQ_HOST

    rabbit_port = os.getenv(RABBITMQ_PORT_ENV_VAR)
    if rabbit_port is None:
        logger.warning(
            f"🐇 env.var '{RABBITMQ_PORT_ENV_VAR}' not set. "
            f"Defaulting to: '{DEFAULT_RABBITMQ_PORT}'"
        )
        rabbit_port = DEFAULT_RABBITMQ_PORT

    return rabbit_host, int(rabbit_port)


def get_q_count(channel, q_name):
    return channel.queue_declare(queue=q_name, passive=True).method.message_count


def wait_on_q_limit(channel: BlockingChannel, q_name: str, lim: int, sleep: int = 10):
    msg_in_q = get_q_count(channel, q_name)
    logger.info(f"🐇 Found {msg_in_q} messages in the queue ({q_name})...")
    while msg_in_q > lim:
        logger.debug(f"🐇 Waiting... ({msg_in_q} remaining)")
        time.sleep(sleep)
        msg_in_q = get_q_count(channel, q_name)


class BaseQueueClient:
    VALID_EXCHANGE_TYPES = ["fanout", "topic", "headers"]
    DEFAULT_TCP_KEEPIDLE = 60 * 5  # 5 minutes

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        blocked_timeout: int = 10,
        q_lim: Optional[int] = None,
        *args,
        **kwargs,
    ):
        # super().__init__(*args, **kwargs)
        self.queue_name = None
        self.exchange_name = None
        self.exchange_type = None
        self.host = host
        self.port = port
        self._timeout = blocked_timeout
        self.q_lim = q_lim or -1

    def _validate_params(self):
        if self.queue_name and self.exchange_name:
            logger.notice("🐇 Connecting to an exchange and a queue simultanously")  # type: ignore

        if self.exchange_name and self.exchange_type not in self.VALID_EXCHANGE_TYPES:
            raise ValueError(
                f"Invalid exchange type: '{self.exchange_type}'. "
                f"Must be one of: {self.VALID_EXCHANGE_TYPES}"
            )
        if self.q_lim > 0 and self.exchange_name:
            logger.warning("🐇 Queue limit will be ignored when sending to an exchange")

        logger.info(
            f"🐇 @ {self.host}:{self.port} "
            f"| queue: {self.queue_name} "
            f"| exchange: {self.exchange_name}"
        )

    def declare_queue(
        self,
        channel: BlockingChannel,
        queue_name: str,
        passive: bool = False,
        durable: bool = False,
        exclusive: bool = False,
        auto_delete: bool = False,
    ) -> None:
        # Create the channel **persistent** queue
        logger.debug(f"🐇 Connecting to queue: {self.queue_name}")
        channel.queue_declare(
            queue=queue_name,
            passive=passive,  # message persistance
            durable=durable,  # message persistance
            exclusive=exclusive,  # so we can reconnect after a consumer restart
            auto_delete=auto_delete,  # queue survives consumer restart
        )

    def declare_exchange(
        self,
        channel: BlockingChannel,
        exchange_name: str,
        exchange_type: str,
        durable: bool = False,
    ) -> None:
        logger.debug(
            f"🐇 Connecting to a '{self.exchange_type}' exchange: {self.exchange_name}"
        )
        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type=exchange_type,
            durable=durable,
        )

    def connect(
        self, tcp_keepidle: Optional[int] = None
    ) -> tuple[pika.BlockingConnection, BlockingChannel]:
        tcp_options = {"TCP_KEEPIDLE": tcp_keepidle or self.DEFAULT_TCP_KEEPIDLE}
        connection = pika.BlockingConnection(
            # for connection no to die while blocked waiting for inputs
            # we must set the heartbeat to 0 (although is discouraged)
            pika.ConnectionParameters(
                self.host,
                self.port,
                blocked_connection_timeout=self._timeout,
                heartbeat=0,
                tcp_options=tcp_options,
            )
        )
        channel = connection.channel()

        return connection, channel


class BlockingQueuePublisher(BaseQueueClient):
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        queue_name: Optional[str] = None,
        exchange_name: Optional[str] = None,
        exchange_type: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(host, port, *args, **kwargs)
        self.queue_name = queue_name
        self.exchange_name = exchange_name or ""
        self.exchange_type = exchange_type

    def send_message(self, message, topic: Optional[str] = None):
        connection, channel = self.connect()
        if self.exchange_name and self.exchange_type:
            self.declare_exchange(
                channel, self.exchange_name, self.exchange_type, durable=True
            )

        if self.queue_name:
            # If a queue_name is given but doesn't exist, will fail
            self.declare_queue(channel, self.queue_name, passive=True)

            if self.q_lim > 0:
                wait_on_q_limit(channel, self.queue_name, lim=self.q_lim)

        logger.debug(
            f"Publishing to: {self.exchange_name} | q:{self.queue_name} (topic:{topic})"
        )
        channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=topic,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,
            ),  # make message persistent
        )

        connection.close()
        logger.debug("🐇🍻 Sent!")


class BlockingQueueConsumer(BaseQueueClient):
    PREFETCH_COUNT = 10

    def __init__(
        self,
        on_event: Callable,
        on_done: Callable,
        load_func: Callable,
        queue_name: Optional[str] = None,
        exchange_name: Optional[str] = None,
        exchange_type: Optional[str] = None,
        routing_keys: Optional[list] = None,
        prefetch_count: Optional[int] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        *args,
        **kwargs,
    ):
        super().__init__(
            host,
            port,
            *args,
            **kwargs,
        )

        self._on_event = on_event
        self._on_done = on_done
        self._load_func = load_func
        self.routing_keys = routing_keys
        self.queue_name = queue_name
        self.exchange_name = exchange_name or ""
        self.exchange_type = exchange_type

        self._prefetch_count = prefetch_count or self.PREFETCH_COUNT

        self._validate_params()
        self._connection, self._channel = self.connect()

        self._bind()

    def _bind(self):
        # Connecting directly to a Queue
        result = self._channel.queue_declare(
            queue=self.queue_name or "", durable=True, passive=False
        )
        self.queue_name = result.method.queue
        self._channel.basic_qos(prefetch_count=self._prefetch_count)

        if self.exchange_name and self.exchange_type:
            # Connect to an exchange and bind to the given topics
            self.declare_exchange(
                self._channel, self.exchange_name, self.exchange_type, durable=True
            )
            for k in self.routing_keys:
                logger.info(f"🐇 Binding queue '{self.queue_name}' to key: '{k}'")
                self._channel.queue_bind(
                    exchange=self.exchange_name, queue=self.queue_name, routing_key=k
                )

    def _callback(self, ch, method, properties, body):
        """Assumes a 'body' is an encoded list of data. For each element
        the 'on_event' function is called to process the messages
        """
        try:
            rx_data = self._load_func(body)
            for event in rx_data:
                self._on_event(event)
        except Exception as e:
            logger.exception(f"🐇 Error in queue callback: {e}")
        else:
            # Notify Inference Server via endpoint
            self._on_done()
        finally:
            # Send basic acknowledge back (no matter what)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug("🐇 Done!")

    def consume(self):
        self._channel.basic_consume(
            queue=self.queue_name, on_message_callback=self._callback
        )
        logger.debug(
            f"🐇 Waiting for messages on {self.queue_name}. To exit press CTRL+C"
        )
        self._channel.start_consuming()

    def unbind(self):
        for k in self.routing_keys:
            logger.debug(f"🐇 Unbinding queue '{self.queue_name}' and key: '{k}'")
            self._channel.queue_unbind(
                exchange=self.exchange_name, queue=self.queue_name, routing_key=k
            )

    def close(self):
        logger.info("🐇 Closing connection!")
        self._connection.close()
