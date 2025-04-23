import os
from pathlib import Path
from .boilerplates import sumoplainxml

folder = 'sumo-config'


class SUMOHelper(object):

    def __init__(self, topology):
        filename = topology.name
        Path(folder).mkdir(parents=True, exist_ok=True)

        self.nodes_file_path = os.path.join(folder, filename + ".nod.xml")
        self.edges_file_path = os.path.join(folder, filename + ".edg.xml")
        self.connections_file_path = os.path.join(folder, filename + ".con.xml")

        self.routes_file_name = filename + ".routes.xml"
        self.routes_file_path = os.path.join(folder, self.routes_file_name)

        self.net_file_name = filename + ".net.xml"
        self.net_file_path = os.path.join(folder, self.net_file_name)

        self.sumocfg_file_name = filename + ".scenario.sumocfg"
        self.sumocfg_file_path = os.path.join(folder, self.sumocfg_file_name)

    def create_output(self, converter):
        self.write_nodes(converter.points, converter.signals)
        self.write_edges(converter.tracks)
        self.write_connections_from_nodes(converter.points, converter.signals)
        self.write_routes(converter.routes)
        self.run_netconvert()
        self.write_sumo_scenario_config()

    def write_file(self, file_path, content):
        with open(file_path, 'w') as file:
            print(content, file=file)

    def write_nodes(self, points, signals):
        with open(self.nodes_file_path, 'w') as node_file:
            print("<nodes>", file=node_file)
            for top_knoten_uuid in points:
                print(sumoplainxml.get_sumo_junction_xml(points[top_knoten_uuid]), file=node_file)
            for signal_uuid in signals:
                print(sumoplainxml.get_sumo_signal_xml(signals[signal_uuid]), file=node_file)
            print("</nodes>", file=node_file)

    def write_edges(self, edges):
        with open(self.edges_file_path, 'w') as edge_file:
            print("<edges>", file=edge_file)
            for top_kante_uuid in edges:
                for track_in_top_kante in edges[top_kante_uuid]:
                    print(sumoplainxml.get_sumo_edge_xml(track_in_top_kante), file=edge_file)
            print("</edges>", file=edge_file)

    def write_connections_from_nodes(self, points, signals):
        with open(self.connections_file_path, 'w') as connections_file:
            print("<connections>", file=connections_file)
            for top_knoten_uuid in points:
                print(sumoplainxml.get_sumo_point_connection_xml(points[top_knoten_uuid]), file=connections_file)
            for signal_uuid in signals:
                print(sumoplainxml.get_sumo_signal_connection_xml(signals[signal_uuid]), file=connections_file)
            print("</connections>", file=connections_file)

    def write_routes(self, _routes):
        with open(self.routes_file_path, 'w') as routes_file:
            routes_as_xml = []
            for running_track_uuid in _routes:
                running_track = _routes[running_track_uuid]
                routes_as_xml.append(sumoplainxml.get_sumo_route_xml(running_track))
            print(sumoplainxml.get_routes_boilerplate_xml(routes_as_xml), file=routes_file)

    def write_sumo_scenario_config(self):
        self.write_file(self.sumocfg_file_path,
                        sumoplainxml.get_sumocfg_boilerplate_xml(self.net_file_name, self.routes_file_name))

    def run_netconvert(self):
        command = ["netconvert",
                   f"-n {self.nodes_file_path}",
                   f"-e {self.edges_file_path}",
                   f"-x {self.connections_file_path}",
                   "--railway.topology.repair true",
                   "--railway.topology.repair.connect-straight true",
                   "--railway.topology.all-bidi false",
                   f"-o {self.net_file_path}",
                   "--junctions.minimal-shape",
                   "--no-internal-links"]
        os.system(" ".join(command))