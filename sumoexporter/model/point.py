class Point(object):

    def __init__(self, top_knoten_uuid, geo_knoten_uuid):
        self.top_knoten_uuid = top_knoten_uuid
        self.geo_knoten_uuid = geo_knoten_uuid
        self.id = top_knoten_uuid[-5:]
        self.left = None
        self.right = None
        self.head = None
        self.x = 0
        self.y = 0

    def is_point(self):
        return True

    def get_connected_node(self, top_kante_uuid):
        if self.left is not None and self.left.top_kante_uuid == top_kante_uuid:
            return self.left
        if self.right is not None and self.right.top_kante_uuid == top_kante_uuid:
            return self.right
        if self.head is not None and self.head.top_kante_uuid == top_kante_uuid:
            return self.head
        return None

    def __str__(self):
        return self.top_knoten_uuid
