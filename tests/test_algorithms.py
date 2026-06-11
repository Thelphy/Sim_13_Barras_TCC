import sys
from main import MainController
from engine_sep import PowerSystemEngine
import pandapower as pp

controller = MainController()
controller.state.buses[692].p_load_kw = 180.0

engine = PowerSystemEngine()
engine.build_network(controller.state)

try:
    pp.runpp(engine.net, numba=False)
    print("Default nr: True")
except Exception as e:
    print("Default nr: False", e)

try:
    pp.runpp(engine.net, algorithm='gs', numba=False)
    print("GS: True")
except Exception as e:
    print("GS: False", e)

try:
    pp.runpp(engine.net, algorithm='fdbx', numba=False)
    print("FDBX: True")
except Exception as e:
    print("FDBX: False", e)

try:
    pp.runpp(engine.net, enforce_q_lims=True, numba=False)
    print("enforce q: True")
except Exception as e:
    print("enforce q: False", e)

