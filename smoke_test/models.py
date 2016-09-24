from goblin import element, properties


class Node(element.Vertex):
    nx_id = properties.Property(properties.Integer)
    timestamp = properties.Property(properties.String)


class Edge(element.Edge):
    timestamp = properties.Property(properties.String)
