from planpro_importer import PlanProVersion, import_planpro
from sumoexporter import SUMOExporter
from railwayroutegenerator.routegenerator import RouteGenerator

# Using PlanPro as Data Source
topology = import_planpro("MVP", PlanProVersion.PlanPro19)

# Processor
generator = RouteGenerator(topology)
generator.generate_routes()

# Export to a SUMO Simulation Model
sumo_exporter = SUMOExporter(topology)
sumo_exporter.convert()
sumo_exporter.write_output()
