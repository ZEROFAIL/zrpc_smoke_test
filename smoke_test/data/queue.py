import asyncio
import logging
import os

import click
from aiohttp import web

from smoke_test import constants


logger = logging.getLogger(__name__)


logging.basicConfig(
    format=constants.LOG_FORMAT,
    datefmt=constants.LOG_DATE_FORMAT,
    level=logging.INFO)



def fill_queue(filename):
    queue = asyncio.Queue()
    with open(filename, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            queue.put_nowait(line)
    return queue


dirname = os.path.dirname(os.path.dirname(__file__))
edgefile = dirname + '/data/edges.txt'
queue = fill_queue(edgefile)



async def get(request):
    try:
        line = queue.get_nowait()
    except asyncio.QueueEmpty:
        line = b''
    logger.info('Sending edge: {}'.format(line))
    return web.Response(text=line)


@click.command()
def cli():
    loop = asyncio.get_event_loop()
    app = web.Application(loop=loop)
    app.router.add_get('/', get)
    try:
        web.run_app(app)
    except KeyboardInterrupt:
        raise
    finally:
        loop.close()
