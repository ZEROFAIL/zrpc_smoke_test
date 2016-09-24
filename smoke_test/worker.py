import asyncio
import logging

import click
from goblin import Goblin
from zmq import asyncio as zmq_asyncio
from zrpc import rpc
from zrpc import worker

from smoke_test import constants, models


logger = logging.getLogger(__name__)

logging.basicConfig(
    format=constants.LOG_FORMAT,
    datefmt=constants.LOG_DATE_FORMAT,
    level=logging.DEBUG)


# Setup
loop = zmq_asyncio.ZMQEventLoop()
asyncio.set_event_loop(loop)

app = loop.run_until_complete(Goblin.open(loop))
app.register(models.Node, models.Edge)
app.config_from_file('conf/config.yml')


# Service RPC method defintions
async def echo(request, response):
    response.write_final(request)


async def yield_edge(request, response):
    pass


async def create_edge(request, response):
    pass


async def stream_nodes(request, response):
    pass


async def stream_edges(request, response):
    pass


rpc_methods = {
    'echo': rpc.RPCMethodSpecification(
        implementation=echo,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x),
    'yield_edge': rpc.RPCMethodSpecification(
        implementation=yield_edge,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x),
    'create_edge': rpc.RPCMethodSpecification(
        implementation=echo,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x),
    'stream_nodes': rpc.RPCMethodSpecification(
        implementation=stream_nodes,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x),
    'stream_edges': rpc.RPCMethodSpecification(
        implementation=stream_edges,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x),
}


# Run a worker
@click.command()
@click.option('--broker', '-b', default='tcp://127.0.0.1:5555',
              help='broker backend endpoint')
@click.option('--service', '-s', default='smoke_test_service',
              help='service name')
def cli(broker, service):
    handler = rpc.RPCRequestHandler(rpc_methods, service.encode('utf-8'), loop)
    rpc_worker = worker.RPCWorker(broker=broker, rpc_handler=handler, loop=loop)
    loop.run_until_complete(rpc_worker.connect())
    task = rpc_worker.run()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        task.cancel()
        loop.run_until_complete(app.close())
        try:
            # Finish tasks and consume cancelation erros
            loop.run_until_complete(task)
        except:
            pass
        finally:
            raise
    finally:
        loop.close()
