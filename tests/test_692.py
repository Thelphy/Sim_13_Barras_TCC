import sys
from main import MainController
from engine_sep import PowerSystemEngine

controller = MainController()
controller.state.buses[692].p_load_kw = 180.0

engine = PowerSystemEngine()
engine.build_network(controller.state)
engine.run_power_flow()

print("Result Load 692 change:", engine.results.success)
