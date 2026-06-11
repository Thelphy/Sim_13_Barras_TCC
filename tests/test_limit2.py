import sys
from main import MainController
from engine_sep import PowerSystemEngine
import pandapower as pp

for load_val in range(170, 190, 1):
    controller = MainController()
    controller.state.buses[692].p_load_kw = float(load_val)
    
    # Increase switch impedance to avoid ill-conditioning
    controller.state.lines[10].r_ohm_per_km = 0.1
    controller.state.lines[10].x_ohm_per_km = 0.1

    engine = PowerSystemEngine()
    engine.build_network(controller.state)
    try:
        pp.runpp(engine.net, numba=False)
        print(f"Load {load_val} kW: Converged.")
    except:
        print(f"Load {load_val} kW: Diverged.")
