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


# All of these methods should have error handling code in real life
async def build(rpc_client):
    rpc_client.connect()
    while True:
        try:
            resp = await asyncio.wait_for(rpc_client.call('yield_edge', b''), 1)
            msg = await asyncio.wait_for(resp.get(), 1)
        except:
            await asyncio.sleep(5)
            pass
        else:
            if not msg:
                logger.info('SUCCESS! READ ALL EDGES FROM DATABASE')
                break
            logger.info('retreieved {} from datastore'.format(msg.body))
            try:
                resp = await asyncio.wait_for(
                    rpc_client.call('create_edge', msg.body), 1)
                msg = await asyncio.wait_for(resp.get(), 1)
            except:
                await asyncio.sleep(5)
                pass
            else:
                logger.info("{} in TinkerGraph".format(msg.body))


async def nodes(rpc_client):
    rpc_client.connect()
    while True:
        try:
            resp = await asyncio.wait_for(
                rpc_client.call('stream_nodes', b''), 1)
            while True:
                msg = await asyncio.wait_for(resp.get(), 1)
                if not msg.body:
                    break
                logger.info('Retrieved {}'.format(msg.body))
                # This makes the build task a priority
            logger.info(
                '***********RETRIEVED ALL NODES...SLEEPING...***********')
        except:
            await asyncio.sleep(5)
            continue
        else:
            await asyncio.sleep(3)


async def edges(rpc_client):
    rpc_client.connect()
    while True:
        try:
            resp = await asyncio.wait_for(
                rpc_client.call('stream_edges', b''), 1)
            while True:
                msg = await resp.get()
                if not msg.body:
                    break
                logger.info('Retrieved {}'.format(msg.body))
                # This makes the build task a priority
            logger.info(
                '***********RETRIEVED ALL EDGES...SLEEPING...***********')
        except:
            await asyncio.sleep(5)
            continue
        else:
            await asyncio.sleep(3)


tasks = {
    'build': ('create', build),
    'nodes': ('streaming', nodes),
    'edges': ('streaming', edges)}


@click.command()
@click.option('--broker', '-b', multiple=True, default=['tcp://127.0.0.1:5556'],
              help='multiple broker TCP endpoints')
@click.option('--service', '-s', default='smoke_test_service',
              help='service name')
@click.option('--task', '-t', default='nodes',
              type=click.Choice(['build', 'nodes', 'edges']),
              help='task performed by client')
def cli(broker, service, task):
    logger.warn(broker)
    loop = zmq_asyncio.ZMQEventLoop()
    asyncio.set_event_loop(loop)
    service, task = tasks[task]
    rpc_client = client.RPCClient(broker, service.encode('utf-8'), loop)
    task = loop.create_task(task(rpc_client))
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
