class Track(object):
    def __init__(self, top_kante_uuid, top_kanten_track_counter):
        self.top_kante_uuid = top_kante_uuid
        self.id = f"{top_kante_uuid[-5:]}-{top_kanten_track_counter}"
        self.re_id = self.id + "-re"
        self.top_kante_length = 0
        self.left_point = None
        self.right_point = None
        self.geo_kanten = []
        self.signals = None
        self.shape_coordinates = []

    def add_shape_coordinates(self, new_coordinates):
        self.shape_coordinates.append(new_coordinates)

    def __str__(self):
        return self.top_kante_uuid
