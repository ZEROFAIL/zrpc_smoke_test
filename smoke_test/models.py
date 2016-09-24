from goblin import element, properties


class Node(element.Vertex):

    nx_id = properties.Property(properties.Integer)
    timestamp = properties.Property(properties.Float)

    def __init__(self, nx_id=None, timestamp=None):
        self._nx_id = nx_id
        self._timestamp = timestamp


class Edge(element.Edge):

    timestamp = properties.Property(properties.Float)

    def __init__(self, source=None, target=None, timestamp=None):
        self._source = source
        self._target = target
        self._timestamp = timestamp
