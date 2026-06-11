import sys
from main import MainController
from engine_sep import PowerSystemEngine
import pandapower as pp

controller = MainController()

for load_val in range(170, 200, 1):
    controller.state.buses[692].p_load_kw = float(load_val)
    
    # Use a well-conditioned value for the switch
    controller.state.lines[10].r_ohm_per_km = 0.01
    controller.state.lines[10].x_ohm_per_km = 0.01

    engine = PowerSystemEngine()
    engine.build_network(controller.state)
    try:
        pp.runpp(engine.net, numba=False)
        print(f"Load {load_val} kW: Converged. V={engine.net.res_bus.loc[engine.bus_mapping[692], 'vm_pu']}")
    except:
        print(f"Load {load_val} kW: Diverged.")
