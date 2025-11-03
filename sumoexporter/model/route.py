from random import randint


class Route(object):
    def __init__(self, route_uuid):
        self.route_uuid = route_uuid
        self.id = "route_none-none"
        self.start_signal = None
        self.end_signal = None
        self.track_ids = []

        r = randint(0, 255)
        g = randint(0, 255)
        b = randint(0, 255)
        self.color = f"{r},{g},{b}"

    def update_id(self):
        first_part = "none"
        second_part = "none"
        if self.start_signal is not None:
            first_part = self.start_signal.id.upper()
        if self.end_signal is not None:
            second_part = self.end_signal.id.upper()
        self.id = f"route_{first_part}-{second_part}"
