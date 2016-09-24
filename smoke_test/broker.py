import asyncio
import logging

import click

from zmq import asyncio as zmq_asyncio
from zrpc import broker

from smoke_test import constants


logger = logging.getLogger(__name__)


logging.basicConfig(
    format=constants.LOG_FORMAT,
    datefmt=constants.LOG_DATE_FORMAT,
    level=logging.DEBUG)



@click.command()
@click.option('--frontend', default='tcp://127.0.0.1:5556',
              help="frontend TCP endpoint")
@click.option('--backend', default='tcp://127.0.0.1:5555',
              help="backend TCP endpoint")
def cli(frontend, backend):
    loop = zmq_asyncio.ZMQEventLoop()
    asyncio.set_event_loop(loop)

    rpc_broker = broker.Broker(loop)
    rpc_broker.bind(frontend, backend)

    tasks = asyncio.gather(rpc_broker.handle_frontend(),
                           rpc_broker.handle_backend(), loop=loop)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        tasks.cancel()
        raise
    finally:
        loop.close()
