import asyncio
import logging

import click
from zmq import asyncio as zmq_asyncio
from zrpc import rpc, client

from smoke_test import constants

logger = logging.getLogger(__name__)


logging.basicConfig(
    format=constants.LOG_FORMAT,
    datefmt=constants.LOG_DATE_FORMAT,
    level=logging.INFO)


async def run(rpc_client):
    rpc_client.connect()
    while True:
        await asyncio.sleep(0.1)
        resp = await rpc_client.call('echo', b'hello')
        while True:
            msg = await resp.get()
            if msg.final:
                break
        logger.info(msg)


@click.command()
@click.option('--broker', '-b', default='tcp://127.0.0.1:5556',
              help='multiple broker TCP endpoints')
@click.option('--service', '-s', default='smoke_test_service',
              help='service name')
def cli(broker, service):
    loop = zmq_asyncio.ZMQEventLoop()
    asyncio.set_event_loop(loop)
    rpc_client = client.RPCClient(broker, service.encode('utf-8'), loop)
    task = loop.create_task(run(rpc_client))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        rpc_client.close()
        task.cancel()
        try:
            loop.run_until_complete(task)
        except:
            pass
        finally:
            raise
    finally:
        loop.close()
