import sys
from main import MainController
from engine_sep import PowerSystemEngine
import copy

controller = MainController()

# Set an extreme parameter that causes divergence to see what prints
controller.state.buses[645].p_load_kw = 50000.0  # huge load

engine = PowerSystemEngine()
engine.build_network(controller.state)
engine.run_power_flow()

print("Result:", engine.results.success)
