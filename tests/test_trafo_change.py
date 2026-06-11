import sys
from main import MainController
from engine_sep import PowerSystemEngine

controller = MainController()

# Change transformer parameter
controller.state.lines[5].sn_mva = 0.55

engine = PowerSystemEngine()
engine.build_network(controller.state)
engine.run_power_flow()

print("Result Trafo change:", engine.results.success)

# Change a load
controller.state.buses[671].p_load_kw = 1160.0
engine = PowerSystemEngine()
engine.build_network(controller.state)
engine.run_power_flow()
print("Result Load change:", engine.results.success)

