import math
from typing import List

from .model import Point, Track, Route, Signal
from .sumohelper import SUMOHelper
from yaramo.node import EdgeConnectionDirection
from yaramo.signal import SignalDirection


class SUMOExporter(object):

    def __init__(self, topology, add_edge_before_first_signal=True):
        self.topology = topology
        self.add_edge_before_first_signal = add_edge_before_first_signal
        self.points = dict()
        self.tracks = dict()
        self.routes = dict()
        self.signals = dict()

    def convert(self):
        self.convert_topology()
        self.convert_routes()

    def convert_topology(self):
        # Nodes
        def _get_coords_of_yaramo_geo_node(_geo_node):
            _converted_geo_node = _geo_node.to_dbref()
            _x_shift = 4533770.0  # To shift the coordinate system close to 0,0
            _y_shift = 5625780.0
            return _converted_geo_node.x - _x_shift, _converted_geo_node.y - _y_shift

        for yaramo_node_uuid in self.topology.nodes:
            yaramo_node = self.topology.nodes[yaramo_node_uuid]
            point_obj = Point(yaramo_node.uuid, yaramo_node.geo_node.uuid)
            converted_x, converted_y = _get_coords_of_yaramo_geo_node(yaramo_node.geo_node)
            point_obj.x = converted_x
            point_obj.y = converted_y
            self.points[yaramo_node.uuid] = point_obj

        # Tracks and signals
        def _calc_length_of_yaramo_geo_nodes(_geo_node_a, _geo_node_b):
            _x1, _y1 = _get_coords_of_yaramo_geo_node(_geo_node_a)
            _x2, _y2 = _get_coords_of_yaramo_geo_node(_geo_node_b)
            _x_diff = _x2 - _x1
            _y_diff = _y2 - _y1
            return math.sqrt((_x_diff * _x_diff) + (_y_diff * _y_diff))

        for yaramo_edge_uuid in self.topology.edges:
            yaramo_edge = self.topology.edges[yaramo_edge_uuid]
            yaramo_node_a = yaramo_edge.node_a
            yaramo_node_b = yaramo_edge.node_b
            node_a = self.points[yaramo_node_a.uuid]
            node_b = self.points[yaramo_node_b.uuid]

            # Signal
            signals = yaramo_edge.signals
            signal_list = []
            for yaramo_signal in signals:
                sig_id = yaramo_signal.name
                signal_obj = Signal(yaramo_signal.uuid, yaramo_edge.uuid, sig_id)
                signal_obj.distance_from_start = yaramo_signal.distance_edge
                signal_obj.kind = yaramo_signal.kind
                signal_obj.wirkrichtung = yaramo_signal.direction
                signal_obj.top_kante_length = yaramo_edge.length
                signal_list.append(signal_obj)
            signal_list.sort(key=lambda sig: sig.distance_from_start, reverse=False)

            # Create tracks by splits
            tracks_in_order = []
            processed_signals = []
            edge_distance_sum_so_far = 0

            cur_track_top_kanten_counter = 0
            cur_track_obj = Track(yaramo_edge.uuid, cur_track_top_kanten_counter)
            cur_track_obj.left_point = node_a
            cur_track_obj.add_shape_coordinates(f"{node_a.x},{node_a.y}")
            cur_track_obj.top_kante_length = yaramo_edge.length
            tracks_in_order.append(cur_track_obj)
            previous_yaramo_geo_node = yaramo_edge.node_a.geo_node
            missing_nodes = yaramo_edge.intermediate_geo_nodes + [yaramo_node_b.geo_node]

            for inter_yaramo_geo_node in missing_nodes:
                edge_length = _calc_length_of_yaramo_geo_nodes(previous_yaramo_geo_node, inter_yaramo_geo_node)
                for cur_signal in signal_list:
                    if cur_signal.id not in processed_signals and \
                       cur_signal.distance_from_start < edge_distance_sum_so_far + edge_length:
                        # Signal is between the geo nodes

                        x1, y1 = _get_coords_of_yaramo_geo_node(previous_yaramo_geo_node)
                        x2, y2 = _get_coords_of_yaramo_geo_node(inter_yaramo_geo_node)
                        factor = (float(cur_signal.distance_from_start) - edge_distance_sum_so_far) / edge_length
                        cur_signal.x = x1 + (factor * (x2 - x1))
                        cur_signal.y = y1 + (factor * (y2 - y1))

                        cur_signal.left_track = cur_track_obj
                        cur_track_obj.right_point = cur_signal
                        cur_track_obj.add_shape_coordinates(f"{cur_signal.x},{cur_signal.y}")

                        # Create new track
                        cur_track_top_kanten_counter = cur_track_top_kanten_counter + 1
                        cur_track_obj = Track(yaramo_edge.uuid, cur_track_top_kanten_counter)
                        cur_track_obj.add_shape_coordinates(f"{cur_signal.x},{cur_signal.y}")
                        cur_track_obj.top_kante_length = yaramo_edge.length
                        tracks_in_order.append(cur_track_obj)
                        cur_signal.right_track = cur_track_obj
                        cur_track_obj.left_point = cur_signal

                        self.signals[cur_signal.signal_uuid] = cur_signal
                        processed_signals.append(cur_signal.id)

                x, y = _get_coords_of_yaramo_geo_node(inter_yaramo_geo_node)
                cur_track_obj.add_shape_coordinates(f"{x},{y}")
                edge_distance_sum_so_far = edge_distance_sum_so_far + edge_length
                previous_yaramo_geo_node = inter_yaramo_geo_node

            cur_track_obj.right_point = node_b

            anschluss_a = EdgeConnectionDirection.Spitze
            if len(yaramo_node_a.connected_nodes) == 3:
                anschluss_a = yaramo_node_a.get_anschluss_for_edge(yaramo_edge)
                #anschluesse_a = yaramo_node_a.get_anschluss_of_other(yaramo_node_b)

            anschluss_b = EdgeConnectionDirection.Spitze
            if len(yaramo_node_b.connected_nodes) == 3:
                anschluss_b = yaramo_node_b.get_anschluss_for_edge(yaramo_edge)
                #anschluesse_b = yaramo_node_b.get_anschluss_of_other(yaramo_node_a)
            
            #for anschluss in anschluesse_a:
            if anschluss_a == EdgeConnectionDirection.Spitze:
                node_a.head = tracks_in_order[0]
            elif anschluss_a == EdgeConnectionDirection.Links:
                node_a.left = tracks_in_order[0]
            elif anschluss_a == EdgeConnectionDirection.Rechts:
                node_a.right = tracks_in_order[0]
            else:
                raise ValueError("Topology broken. Anschluss not found.")

            #for anschluss in anschluesse_b:
            if anschluss_b == EdgeConnectionDirection.Spitze:
                node_b.head = tracks_in_order[-1]
            elif anschluss_b == EdgeConnectionDirection.Links:
                node_b.left = tracks_in_order[-1]
            elif anschluss_b == EdgeConnectionDirection.Rechts:
                node_b.right = tracks_in_order[-1]
            else:
                raise ValueError("Topology broken. Anschluss not found.")

            self.tracks[yaramo_edge.uuid] = tracks_in_order

    def convert_routes(self):
        def _get_track_ids_in_order(_start_signal, _end_signal, _yaramo_edges_in_order):
            _track_ids = []

            # First edge
            _cur_track = None
            _cur_dir = _start_signal.wirkrichtung
            if _cur_dir == SignalDirection.IN:
                # "in" direction
                _cur_track = _start_signal.right_track
                if self.add_edge_before_first_signal:
                    _track_ids.append(_start_signal.left_track.id)  # To start train before signal
                _track_ids.append(_cur_track.id)
            else:  # "gegen" direction
                _cur_track = _start_signal.left_track
                if self.add_edge_before_first_signal:
                    _track_ids.append(_start_signal.right_track.re_id)  # To start train before signal
                _track_ids.append(_cur_track.re_id)

            # Walk through edges
            while _cur_track is not None:
                # Get next point
                _next_point = _cur_track.right_point
                if _cur_dir == SignalDirection.GEGEN:
                    _next_point = _cur_track.left_point

                if _next_point.id == _end_signal.id:  # End signal found
                    break

                if _next_point.is_point():
                    # Track switch
                    _cur_top_kante_uuid = _cur_track.top_kante_uuid
                    _next_track = None
                    for _yaramo_edge in _yaramo_edges_in_order:
                        if _yaramo_edge.uuid != _cur_top_kante_uuid:
                            _next_track = _next_point.get_connected_track(_yaramo_edge.uuid)
                            if _next_track is not None:
                                break

                    if _next_track is None:
                        raise ValueError(f"Data structure broken, no following TOP Kante on route from {_start_signal.id} to {_end_signal.id} found")

                    _cur_track = _next_track
                    if _cur_track.left_point.id == _next_point.id:
                        # "in" direction
                        _cur_dir = SignalDirection.IN
                    else:  # "gegen" direction
                        _cur_dir = SignalDirection.GEGEN
                else:
                    # Only a signal
                    if _cur_dir == SignalDirection.IN:
                        _cur_track = _next_point.right_track
                    else:
                        _cur_track = _next_point.left_track

                if _cur_dir == SignalDirection.IN:
                    _track_ids.append(_cur_track.id)
                else:
                    _track_ids.append(_cur_track.re_id)

            return _track_ids

        for yaramo_route in self.topology.routes.values():
            route = Route(yaramo_route.uuid)

            # Start and End Signal
            if yaramo_route.start_signal is None or yaramo_route.start_signal.uuid not in self.signals or \
               yaramo_route.end_signal is None or yaramo_route.end_signal.uuid not in self.signals:
                print(f"Skip route because at least one signal not found, route uuid: {yaramo_route.uuid}")
                continue
            route.start_signal = self.signals[yaramo_route.start_signal.uuid]
            route.end_signal = self.signals[yaramo_route.end_signal.uuid]
            route.update_id()

            # Tracks
            route.track_ids = _get_track_ids_in_order(route.start_signal, route.end_signal, yaramo_route.get_edges_in_order())
            self.routes[yaramo_route.uuid] = route

    def write_output(self, output_format="sumo-plain-xml"):
        output_helper = None
        if output_format == "sumo-plain-xml":
            output_helper = SUMOHelper(self.topology)
        if output_helper is None:
            raise NotImplementedError()
        output_helper.create_output(self)
