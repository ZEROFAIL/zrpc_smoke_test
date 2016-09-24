import asyncio
import logging

import aiohttp
import click
from goblin import driver, Goblin
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

cluster = app._cluster


# Service RPC method defintions
async def echo(request, response):
    response.write_final(request)


async def yield_edge(request, response):
    async with aiohttp.ClientSession(loop=loop) as client:
        edge = await client.get('http://localhost:8080/')
        payload = await edge.read()
        logger.info(edge, payload)
        response.write_final(payload)


async def create_edge(request, response):
    time = loop.time()
    session = await app.session()
    source_id, target_id = request.decode('utf-8').split(' ')
    source = models.Node(source_id, time)
    target = models.Node(target_id, time)
    for vertex in [source, target]:
        resp = await session.g.V().has(
            models.Node.nx_id, vertex.nx_id).oneOrNone()
        if not resp:
            session.add(vertex)
        else:
            # This is kind of a hack to use a proxy id (nx_id)
            vertex._id = resp.id
    await session.flush()
    assert source.id
    assert target.id
    edge = models.Edge(source, target, time)
    session.add(edge)
    await session.flush()
    msg = "Created edge {}: ({})->({}) at {} o'clock".format(
        edge.id, source.id, target.id, time).encode('utf-8')
    response.write_final(msg)



async def stream_nodes(request, response):
    client = await cluster.connect()
    g = driver.AsyncGraph().traversal().withRemote(client)
    async for msg in g.V():
        vid = msg['id']
        nx_id = msg['properties']['nx_id'][0]['value']
        time = msg['properties']['timestamp'][0]['value']
        msg = "Vertex: {} - nx_id={}, created at {} o'clock".format(
            vid, nx_id, time)
        response.write(msg.encode('utf-8'))
    response.write_final(b'')


async def stream_edges(request, response):
    client = await cluster.connect()
    g = driver.AsyncGraph().traversal().withRemote(client)
    async for msg in g.E():
        eid = msg['id']
        time = msg['properties']['timestamp']
        msg = "Edge: {} created at {} o'clock".format(eid, time)
        response.write(msg.encode('utf-8'))
    response.write_final(b'')


create_service_methods = {
    'echo': rpc.RPCMethodSpecification(
        implementation=echo,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x),
    'yield_edge': rpc.RPCMethodSpecification(
        implementation=yield_edge,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x),
    'create_edge': rpc.RPCMethodSpecification(
        implementation=create_edge,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x),
}


streaming_service_methods = {
    'stream_nodes': rpc.RPCMethodSpecification(
        implementation=stream_nodes,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x),
    'stream_edges': rpc.RPCMethodSpecification(
        implementation=stream_edges,
        request_deserializer=lambda x: x,
        reply_serializer=lambda x: x)
}


services = {
    'create': create_service_methods,
    'streaming': streaming_service_methods
}


# Run a worker
@click.command()
@click.option('--broker', '-b', default='tcp://127.0.0.1:5555',
              help='broker backend endpoint')
@click.option('--service', '-s', default='streaming',
              type=click.Choice(['streaming', 'create']), help='service name')
def cli(broker, service):
    rpc_methods = services[service]
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
