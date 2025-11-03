from planpro_importer import PlanProVersion, import_planpro
from railwayroutegenerator.routegenerator import RouteGenerator
from yaramo.model import (Edge, EuclideanGeoNode, Node, Route, Signal,
                          SignalDirection, SignalFunction, SignalKind,
                          Topology, Track, TrackType)

from sumoexporter import SUMOExporter

# Using PlanPro as Data Source
topology = import_planpro("MVP", PlanProVersion.PlanPro19)

# Processor
generator = RouteGenerator(topology)
generator.generate_routes()

# Export to a SUMO Simulation Model
sumo_exporter = SUMOExporter(topology)
sumo_exporter.convert()
sumo_exporter.write_output()
