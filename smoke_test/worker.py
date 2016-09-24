import asyncio
import logging

import click
from zmq import asyncio as zmq_asyncio
from zrpc import rpc
from zrpc import worker

from smoke_test import constants


logger = logging.getLogger(__name__)

logging.basicConfig(
    format=constants.LOG_FORMAT,
    datefmt=constants.LOG_DATE_FORMAT,
    level=logging.DEBUG)


async def echo(request, response):
    response.write_final(request)


rpc_methods = {
    'echo': rpc.RPCMethodSpecification(
        implementation=echo,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x)}


async def run(rpc_worker):

    rpc_worker.run_worker()


@click.command()
@click.option('--broker', default='tcp://127.0.0.1:5555',
              help='broker backend endpoint')
@click.option('--service', default='echo_service', help='service name')
def cli(broker, service):
    loop = zmq_asyncio.ZMQEventLoop()
    asyncio.set_event_loop(loop)

    handler = rpc.RPCRequestHandler(rpc_methods, service.encode('utf-8'), loop)

    rpc_worker = worker.RPCWorker(broker=broker,rpc_handler=handler, loop=loop)
    loop.run_until_complete(rpc_worker.connect())
    task = loop.create_task(rpc_worker.run())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        task.cancel()
        try:
            loop.run_until_complete(task)
        except:
            pass
        finally:
            raise
    finally:
        loop.close()
