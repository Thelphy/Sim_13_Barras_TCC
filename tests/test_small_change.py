import sys
from main import MainController
from engine_sep import PowerSystemEngine

controller = MainController()

# Just change something very small
controller.state.buses[645].p_load_kw = 171.0
controller.state.lines[1].length_km = 0.61

engine = PowerSystemEngine()
engine.build_network(controller.state)
engine.run_power_flow()
print("Success after small change:", engine.results.success)

if not engine.results.success:
    print("Power flow failed to converge!")
