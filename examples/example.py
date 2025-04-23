from planpro_importer.reader import PlanProReader
from sumoexporter import SUMOExporter
from railwayroutegenerator.routegenerator import RouteGenerator

# Using PlanPro as Data Source
reader = PlanProReader("MVP")
topology = reader.read_topology_from_plan_pro_file()

# Processor
generator = RouteGenerator(topology)
generator.generate_routes()

# Export to a SUMO Simulation Model
sumo_exporter = SUMOExporter(topology)
sumo_exporter.convert()
sumo_exporter.write_output()
