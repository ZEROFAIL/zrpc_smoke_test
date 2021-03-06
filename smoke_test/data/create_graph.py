import logging
import os

import click
import networkx as nx

from smoke_test import constants


logger = logging.getLogger(__name__)

logging.basicConfig(
    format=constants.LOG_FORMAT,
    datefmt=constants.LOG_DATE_FORMAT,
    level=logging.INFO)


dirname = os.path.dirname(os.path.dirname(__file__))


@click.command()
@click.option('--nodes', default=10000,
              help='number of nodes in random graph')
@click.option('--prob', default=0.01,
              help='probability of edge creeation')
@click.option('--output', default=dirname + '/data/edges.txt',
              help='the name of the output file')
def cli(nodes, prob, output):
    graph = nx.gnp_random_graph(nodes, prob)
    logger.info("Created graph with {} nodes and {} edges".format(
        len(graph.nodes()), len(graph.edges())))
    logger.info('Storing graph data in: {}'.format(output))
    with open(output, 'w') as f:
        for source, target in graph.edges_iter():
            f.write('{} {}\n'.format(source, target))
