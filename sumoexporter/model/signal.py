class Signal(object):

    def __init__(self, signal_uuid, top_kante_uuid, signal_id):
        self.signal_uuid = signal_uuid
        self.top_kante_uuid = top_kante_uuid
        self.top_kante_length = 0
        self.id = signal_id.replace(" ", "-")
        self.x = None
        self.y = None
        self.distance_from_start = None
        self.kind = None
        self.wirkrichtung = None
        self.left_track = None
        self.right_track = None

    def is_point(self):
        return False
