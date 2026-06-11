import sys
import time
from main import MainController
from engine_sep import PowerSystemEngine
import pandapower as pp

controller = MainController()
engine = PowerSystemEngine()
engine.build_network(controller.state)
engine.run_power_flow()
print("Base power flow success:", engine.results.success)

if engine.results.success:
    for bus_id in ['632', '692']:
        print(f"Starting PV curve for {bus_id}...")
        start = time.time()
        engine.generate_pv_curve(bus_id)
        print(f"PV curve {bus_id} done in {time.time()-start:.2f} seconds")
        print(f"Points generated: {len(engine.results.pv_curve_p)}")
