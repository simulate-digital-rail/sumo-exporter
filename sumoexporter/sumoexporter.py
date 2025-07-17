import math
from typing import List

from .model import Point, Track, Route, Signal
from .sumohelper import SUMOHelper
from yaramo.node import EdgeConnectionDirection
from yaramo.signal import SignalDirection
from yaramo.model import Wgs84GeoNode, DbrefGeoNode, EuclideanGeoNode


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
        def _get_shifted_coords_of_yaramo_geo_node(_geo_node):
            _converted_geo_node = _geo_node.to_dbref().to_euclidean()
            return _converted_geo_node.x, _converted_geo_node.y

        def _get_shifted_coords_by_type(_x, _y, _type):
            if _type == Wgs84GeoNode:
                return _get_shifted_coords_of_yaramo_geo_node(Wgs84GeoNode(_x, _y))
            elif _type == DbrefGeoNode:
                return _get_shifted_coords_of_yaramo_geo_node(DbrefGeoNode(_x, _y))
            else:
                return _get_shifted_coords_of_yaramo_geo_node(EuclideanGeoNode(_x, _y))

        for yaramo_node in self.topology.nodes.values():
            point_obj = Point(yaramo_node.uuid, yaramo_node.geo_node.uuid, yaramo_node.name)
            point_obj.x, point_obj.y = _get_shifted_coords_of_yaramo_geo_node(yaramo_node.geo_node)
            self.points[yaramo_node.uuid] = point_obj

        # Tracks and signals
        for yaramo_edge in self.topology.edges.values():
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
                edge_length = previous_yaramo_geo_node.get_distance_to_other_geo_node(inter_yaramo_geo_node)
                for cur_signal in signal_list:
                    if cur_signal.id not in processed_signals and \
                       cur_signal.distance_from_start < edge_distance_sum_so_far + edge_length:
                        # Signal is between the geo nodes

                        signal_x, signal_y = yaramo_edge.get_coordinates_on_edge_by_distance_from_start_node(
                            float(cur_signal.distance_from_start))
                        cur_signal.x, cur_signal.y = _get_shifted_coords_by_type(signal_x, signal_y, type(inter_yaramo_geo_node))

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

                x, y = _get_shifted_coords_of_yaramo_geo_node(inter_yaramo_geo_node)
                cur_track_obj.add_shape_coordinates(f"{x},{y}")
                edge_distance_sum_so_far = edge_distance_sum_so_far + edge_length
                previous_yaramo_geo_node = inter_yaramo_geo_node

            cur_track_obj.right_point = node_b

            anschluss_a = EdgeConnectionDirection.Spitze
            if yaramo_node_a.is_point():
                anschluss_a = yaramo_node_a.get_anschluss_for_edge(yaramo_edge)

            anschluss_b = EdgeConnectionDirection.Spitze
            if yaramo_node_b.is_point():
                anschluss_b = yaramo_node_b.get_anschluss_for_edge(yaramo_edge)

            def _set_anschluss(_anschluss, _node, _track):
                if _anschluss == EdgeConnectionDirection.Spitze:
                    _node.head = _track
                elif _anschluss == EdgeConnectionDirection.Links:
                    _node.left = _track
                elif _anschluss == EdgeConnectionDirection.Rechts:
                    _node.right = _track
                else:
                    raise ValueError("Topology broken. Anschluss not found.")

            _set_anschluss(anschluss_a, node_a, tracks_in_order[0])
            _set_anschluss(anschluss_b, node_b, tracks_in_order[-1])

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
